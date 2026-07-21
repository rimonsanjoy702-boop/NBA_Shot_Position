#!/usr/bin/env python3
"""
Hexbin Data Preprocessing Script
=================================
Reads NBA Shot Locations CSV, aggregates shots into hexbin grids per season,
and outputs JSON files for frontend consumption.

Output: public/data/hexbin_season_{season}.json (23 files, ~10 MB total)

Each file structure:
  {
    "season": "1997-98",
    "league": {
      "hexbins": [{x, y, count, fg_pct}, ...],
      "hexbins_by_time": {"0": [...], "1": [...], ..., "7": [...]}
    },
    "teams": {
      "<team_id>": {
        "team_name": "...", "abbr": "...",
        "hexbins": [...], "hexbins_by_time": {...}
      }
    },
    "players": {
      "<player_id>": {
        "player_name": "...", "team_id": ..., "team_abbr": "...",
        "hexbins": [...], "hexbins_by_time": {...}
      }
    }
  }

Usage:
    python hexbin/build_hexbin_data.py

Dependencies: pandas >= 1.5, numpy >= 1.22
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Windows UTF-8 compatibility
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ============================================================================
# Configuration
# ============================================================================

HEX_RADIUS = 15            # coordinate units (~1.44 ft, ~20-22 hexes across half-court)
MIN_COUNT_LEAGUE = 5       # minimum shots per hex for league/team level
MIN_COUNT_PLAYER = 3       # minimum shots per hex for individual players

# Court bounds (coordinate units, half-court only)
X_MIN, X_MAX = -250, 250
Y_MIN, Y_MAX = 0, 470

# Number of time bins (Q1-Q4 × front/back half = 8)
N_TIME_BINS = 8
PERIOD_SECONDS = 12 * 60   # 720 seconds per quarter
TIME_BIN_SECONDS = PERIOD_SECONDS // 2  # 360 seconds = 6 minutes

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "NBA Shot Locations 1997 - 2020.csv"
DATA_PATH = DATA_DIR / "NBA Shot Locations 1997 - 2020.csv"
OUTPUT_DIR = PROJECT_ROOT / "public" / "data"

# 12 preset players (player_id → player_name)
PRESET_PLAYERS: dict[int, str] = {
    201939: "Stephen Curry",
    2544:   "LeBron James",
    893:    "Michael Jordan",
    977:    "Kobe Bryant",
    201935: "James Harden",
    201142: "Kevin Durant",
    202691: "Klay Thompson",
    203081: "Damian Lillard",
    406:    "Shaquille O'Neal",
    2730:   "Dwight Howard",
    202695: "Kawhi Leonard",
    201572: "Brook Lopez",
}

# Team abbreviation lookup (full name → abbreviation)
TEAM_NAME_TO_ABBR = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "New Jersey Nets": "NJN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Vancouver Grizzlies": "VAN",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New Orleans Hornets": "NOH",
    "New Orleans/Oklahoma City Hornets": "NOK",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Seattle SuperSonics": "SEA",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}

# ============================================================================
# Season & Time Helpers
# ============================================================================

def derive_season(game_date: int) -> str:
    """Convert Game Date (YYYYMMDD int) to NBA season label 'YYYY-YY'."""
    year = game_date // 10000
    month = (game_date // 100) % 100
    if month >= 10:
        return f"{year}-{str(year + 1)[2:]}"
    else:
        return f"{year - 1}-{str(year)[2:]}"


def compute_game_seconds(period: int, min_rem: int, sec_rem: int) -> int:
    """
    Compute seconds elapsed in regulation game (0–2880).
    Excludes overtime (period > 4).
    """
    if period > 4:
        return -1  # exclude OT
    seconds_in_period = min_rem * 60 + sec_rem
    seconds_elapsed_in_period = PERIOD_SECONDS - seconds_in_period
    return (period - 1) * PERIOD_SECONDS + seconds_elapsed_in_period


def time_bin_index(game_seconds: int) -> int:
    """Map game seconds to time bin 0–7."""
    if game_seconds < 0:
        return -1
    return min(game_seconds // TIME_BIN_SECONDS, N_TIME_BINS - 1)


# ============================================================================
# Hexbin Math — pointy-top hexagon grid
# ============================================================================

def _compute_hex_centers(x: np.ndarray, y: np.ndarray, size: float
                         ) -> tuple[np.ndarray, np.ndarray]:
    """
    Assign each (x, y) point to its nearest hexagon center.
    Returns (cx, cy) integer arrays of hex center coordinates.
    Uses axial → cube rounding for accurate assignment.
    """
    sqrt3 = math.sqrt(3)

    # Fractional axial coordinates
    q_frac = (sqrt3 / 3.0 * x - 1.0 / 3.0 * y) / size
    r_frac = (2.0 / 3.0 * y) / size

    # Round to integer axial
    q_round = np.round(q_frac).astype(int)
    r_round = np.round(r_frac).astype(int)
    s_frac = -q_frac - r_frac
    s_round = np.round(s_frac).astype(int)

    q_diff = np.abs(q_round.astype(float) - q_frac)
    r_diff = np.abs(r_round.astype(float) - r_frac)
    s_diff = np.abs(s_round.astype(float) - s_frac)

    # Fix the coordinate with largest rounding error (cube rounding)
    fix_q = (q_diff > r_diff) & (q_diff > s_diff)
    fix_r = (~fix_q) & (r_diff > s_diff)

    q_round[fix_q] = -r_round[fix_q] - s_round[fix_q]
    r_round[fix_r] = -q_round[fix_r] - s_round[fix_r]

    # Convert axial → Cartesian center
    cx = np.round(size * (1.5 * q_round)).astype(int)
    cy = np.round(size * (sqrt3 / 2.0 * q_round + sqrt3 * r_round)).astype(int)

    return cx, cy


def build_hexbins(df: pd.DataFrame, hex_radius: int, min_count: int
                  ) -> list[dict]:
    """
    Vectorized hexbin aggregation for a DataFrame subset.

    Parameters
    ----------
    df : pd.DataFrame with columns [X Location, Y Location, Shot Made Flag]
    hex_radius : hexagon radius in coordinate units
    min_count : minimum shots per hex cell to include

    Returns
    -------
    list[dict] : [{"x": int, "y": int, "count": int, "fg_pct": float}, ...]
    """
    if len(df) == 0:
        return []

    x = df["X Location"].values.astype(float)
    y = df["Y Location"].values.astype(float)
    made = df["Shot Made Flag"].values.astype(int)

    # Filter to half-court bounds
    mask = (x >= X_MIN) & (x <= X_MAX) & (y >= Y_MIN) & (y <= Y_MAX)
    x, y, made = x[mask], y[mask], made[mask]

    if len(x) == 0:
        return []

    cx, cy = _compute_hex_centers(x, y, float(hex_radius))

    # Group by hex center and aggregate
    temp = pd.DataFrame({"hx": cx, "hy": cy, "made": made})
    grouped = temp.groupby(["hx", "hy"])

    result: list[dict] = []
    for (hx, hy), grp in grouped:
        total = len(grp)
        if total >= min_count:
            # Filter out cells whose center is outside half-court bounds
            if not (X_MIN <= hx <= X_MAX and Y_MIN <= hy <= Y_MAX):
                continue
            result.append({
                "x": int(hx),
                "y": int(hy),
                "count": total,
                "fg_pct": round(float(grp["made"].sum()) / total, 3),
            })

    return result


# ============================================================================
# Accumulator — incremental aggregation during CSV chunk reading
# ============================================================================

class HexbinAccumulator:
    """
    Accumulates shot data by season, entity, and optionally time bin.
    Structure:
      data[season][entity_key][(hx, hy)] = [made_count, total_count]
    """

    def __init__(self, hex_radius: int):
        self.hex_radius = float(hex_radius)
        # season → (hx, hy) → [made, total]
        self.league: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: [0, 0]))
        # season → team_id → (hx, hy) → [made, total]
        self.teams: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
        # season → player_id → (hx, hy) → [made, total]
        self.players: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
        # season → time_bin → (hx, hy) → [made, total]
        self.league_time: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
        # season → team_id → time_bin → (hx, hy) → [made, total]
        self.teams_time: dict[str, dict] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0]))))
        # season → player_id → time_bin → (hx, hy) → [made, total]
        self.players_time: dict[str, dict] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0]))))

        # Metadata
        self.team_info: dict[int, dict] = {}   # team_id → {name, abbr}
        self.player_team: dict[int, int] = {}   # player_id → team_id (primary)

    def add_chunk(self, df: pd.DataFrame) -> None:
        """Process one CSV chunk: assign hex centers, accumulate counts."""
        x = df["X Location"].values.astype(float)
        y = df["Y Location"].values.astype(float)
        made = df["Shot Made Flag"].values.astype(int)
        game_dates = df["Game Date"].values.astype(int)
        periods = df["Period"].values.astype(int)
        min_rems = df["Minutes Remaining"].values.astype(int)
        sec_rems = df["Seconds Remaining"].values.astype(int)
        team_ids = df["Team ID"].values.astype(int)
        player_ids = df["Player ID"].values.astype(int)
        team_names = df["Team Name"].values.astype(str)
        player_names = df["Player Name"].values.astype(str)

        # Court bounds filter
        mask = (x >= X_MIN) & (x <= X_MAX) & (y >= Y_MIN) & (y <= Y_MAX)
        x, y, made = x[mask], y[mask], made[mask]
        game_dates = game_dates[mask]
        periods, min_rems, sec_rems = periods[mask], min_rems[mask], sec_rems[mask]
        team_ids, player_ids = team_ids[mask], player_ids[mask]
        team_names, player_names = team_names[mask], player_names[mask]

        if len(x) == 0:
            return

        # Compute hex centers
        cx_arr, cy_arr = _compute_hex_centers(x, y, self.hex_radius)

        preset_ids = set(PRESET_PLAYERS.keys())

        for i in range(len(x)):
            season = derive_season(int(game_dates[i]))
            hx = int(cx_arr[i])
            hy = int(cy_arr[i])
            m = int(made[i])
            tid = int(team_ids[i])
            pid = int(player_ids[i])

            # ---- League accumulation ----
            cell = self.league[season][(hx, hy)]
            cell[0] += m
            cell[1] += 1

            # ---- Team accumulation ----
            cell_t = self.teams[season][tid][(hx, hy)]
            cell_t[0] += m
            cell_t[1] += 1

            # Track team info
            if tid not in self.team_info:
                self.team_info[tid] = {
                    "name": str(team_names[i]),
                    "abbr": TEAM_NAME_TO_ABBR.get(str(team_names[i]), str(team_names[i])[:3].upper()),
                }

            # ---- Player accumulation (preset players only) ----
            if pid in preset_ids:
                cell_p = self.players[season][pid][(hx, hy)]
                cell_p[0] += m
                cell_p[1] += 1
                if pid not in self.player_team:
                    self.player_team[pid] = tid

            # ---- Time bin accumulation ----
            gs = compute_game_seconds(int(periods[i]), int(min_rems[i]), int(sec_rems[i]))
            tb = time_bin_index(gs)
            if tb < 0:
                continue  # exclude OT

            # League + time
            cell_lt = self.league_time[season][tb][(hx, hy)]
            cell_lt[0] += m
            cell_lt[1] += 1

            # Team + time
            cell_tt = self.teams_time[season][tid][tb][(hx, hy)]
            cell_tt[0] += m
            cell_tt[1] += 1

            # Player + time
            if pid in preset_ids:
                cell_pt = self.players_time[season][pid][tb][(hx, hy)]
                cell_pt[0] += m
                cell_pt[1] += 1

    def _cells_to_hexbins(self, cells: dict, min_count: int) -> list[dict]:
        """Convert accumulated {(hx, hy): [made, total]} → hexbin list.
        Filters hex cells whose center falls outside court bounds."""
        result: list[dict] = []
        for (hx, hy), (made_sum, total) in cells.items():
            if total >= min_count:
                # Filter out cells whose center is outside half-court bounds
                if not (X_MIN <= hx <= X_MAX and Y_MIN <= hy <= Y_MAX):
                    continue
                result.append({
                    "x": hx,
                    "y": hy,
                    "count": total,
                    "fg_pct": round(made_sum / total, 3),
                })
        return result

    def build_season_json(self, season: str) -> dict:
        """Build the JSON structure for one season."""
        # --- League ---
        league_hexbins = self._cells_to_hexbins(self.league.get(season, {}), MIN_COUNT_LEAGUE)
        league_time: dict[str, list] = {}
        for tb in range(N_TIME_BINS):
            tb_key = str(tb)
            league_time[tb_key] = self._cells_to_hexbins(
                self.league_time.get(season, {}).get(tb, {}), MIN_COUNT_LEAGUE)

        # --- Teams ---
        teams_json: dict[str, dict] = {}
        teams_data = self.teams.get(season, {})
        teams_time_data = self.teams_time.get(season, {})
        for tid in sorted(teams_data.keys()):
            info = self.team_info.get(tid, {"name": f"Team {tid}", "abbr": f"T{tid}"})
            team_entry: dict = {
                "team_name": info["name"],
                "abbr": info["abbr"],
                "hexbins": self._cells_to_hexbins(teams_data[tid], MIN_COUNT_LEAGUE),
                "hexbins_by_time": {},
            }
            for tb in range(N_TIME_BINS):
                tb_key = str(tb)
                team_entry["hexbins_by_time"][tb_key] = self._cells_to_hexbins(
                    teams_time_data.get(tid, {}).get(tb, {}), MIN_COUNT_LEAGUE)
            teams_json[str(tid)] = team_entry

        # --- Players ---
        players_json: dict[str, dict] = {}
        players_data = self.players.get(season, {})
        players_time_data = self.players_time.get(season, {})
        for pid in sorted(players_data.keys()):
            tid = self.player_team.get(pid, 0)
            team_abbr = self.team_info.get(tid, {}).get("abbr", "???")
            player_entry = {
                "player_name": PRESET_PLAYERS.get(pid, f"Player {pid}"),
                "team_id": tid,
                "team_abbr": team_abbr,
                "hexbins": self._cells_to_hexbins(players_data[pid], MIN_COUNT_PLAYER),
                "hexbins_by_time": {},
            }
            for tb in range(N_TIME_BINS):
                tb_key = str(tb)
                player_entry["hexbins_by_time"][tb_key] = self._cells_to_hexbins(
                    players_time_data.get(pid, {}).get(tb, {}), MIN_COUNT_PLAYER)
            players_json[str(pid)] = player_entry

        return {
            "season": season,
            "league": {
                "hexbins": league_hexbins,
                "hexbins_by_time": league_time,
            },
            "teams": teams_json,
            "players": players_json,
        }


# ============================================================================
# Validation
# ============================================================================

def validate_output(output_dir: Path, expected_seasons: int) -> dict:
    """Run the design doc's validation checklist on all output JSON files."""
    print("\n" + "=" * 60)
    print("Output Validation")
    print("=" * 60)

    results = {
        "files_found": 0,
        "files_with_league": 0,
        "fg_pct_ok": True,
        "coords_ok": True,
        "counts_ok": True,
        "players_present": defaultdict(set),  # season → set of player ids
        "total_size_mb": 0.0,
        "files_with_time_bins": 0,
        "time_bins_nonempty": 0,
    }

    json_files = sorted(output_dir.glob("hexbin_season_*.json"))
    results["files_found"] = len(json_files)

    for fp in json_files:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)

        results["total_size_mb"] += fp.stat().st_size / (1024 * 1024)

        season = data.get("season", "")
        league = data.get("league", {})

        # League hexbins non-empty
        if league.get("hexbins"):
            results["files_with_league"] += 1

        # Time bins present
        hbt = league.get("hexbins_by_time", {})
        if len(hbt) == N_TIME_BINS:
            results["files_with_time_bins"] += 1
        for tb_k, tb_data in hbt.items():
            if tb_data:
                results["time_bins_nonempty"] += 1

        # Validate all hexbins
        def check_hexbins(hex_list, label=""):
            for h in hex_list:
                if not (0.0 <= h["fg_pct"] <= 1.0):
                    results["fg_pct_ok"] = False
                    print(f"  ⚠ fg_pct out of range: {h['fg_pct']} in {label}")
                if not (X_MIN <= h["x"] <= X_MAX):
                    results["coords_ok"] = False
                    print(f"  ⚠ x out of range: {h['x']} in {label}")
                if not (Y_MIN <= h["y"] <= Y_MAX):
                    results["coords_ok"] = False
                    print(f"  ⚠ y out of range: {h['y']} in {label}")
                if h["count"] < 1:
                    results["counts_ok"] = False
                    print(f"  ⚠ count < 1: {h['count']} in {label}")

        check_hexbins(league.get("hexbins", []), f"{season}/league")
        for tb_data in league.get("hexbins_by_time", {}).values():
            check_hexbins(tb_data, f"{season}/league/time")

        # Track preset players
        players = data.get("players", {})
        for pid_str in players:
            results["players_present"][season].add(int(pid_str))

    # Print summary
    print(f"  Files found:          {results['files_found']} (expected {expected_seasons})")
    print(f"  Files with league:    {results['files_with_league']}")
    print(f"  Files with time bins: {results['files_with_time_bins']}")
    print(f"  Total size:           {results['total_size_mb']:.1f} MB")
    print(f"  fg_pct in [0,1]:      {'✓' if results['fg_pct_ok'] else '✗ FAIL'}")
    print(f"  Coordinates in bounds:{'✓' if results['coords_ok'] else '✗ FAIL'}")
    print(f"  Counts ≥ 1:           {'✓' if results['counts_ok'] else '✗ FAIL'}")

    # Player presence
    expected_players = set(PRESET_PLAYERS.keys())
    all_good = True
    for season in sorted(results["players_present"]):
        missing = expected_players - results["players_present"][season]
        if missing:
            names = [PRESET_PLAYERS[pid] for pid in missing]
            print(f"  ⚠ {season}: missing players: {names}")
            all_good = False
    if all_good:
        print(f"  12 preset players:     ✓ all present in their active seasons")

    return results


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 60)
    print("NBA Hexbin Data Preprocessing")
    print(f"Hex radius: {HEX_RADIUS} coordinate units")
    print(f"Min count (league/team): {MIN_COUNT_LEAGUE}, (player): {MIN_COUNT_PLAYER}")
    print(f"Data source: {DATA_PATH}")
    print(f"Output dir:  {OUTPUT_DIR}")
    print("=" * 60)

    if not DATA_PATH.exists():
        print(f"\nERROR: Data file not found at {DATA_PATH}")
        sys.exit(1)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Phase 1: Accumulate ----
    print("\n[Phase 1] Reading CSV and accumulating hexbins...")
    t0 = time.time()

    acc = HexbinAccumulator(HEX_RADIUS)
    chunk_size = 200_000
    total_rows = 0

    reader = pd.read_csv(DATA_PATH, chunksize=chunk_size)
    for i, chunk in enumerate(reader):
        acc.add_chunk(chunk)
        total_rows += len(chunk)
        if (i + 1) % 5 == 0:
            elapsed = time.time() - t0
            rate = total_rows / elapsed
            print(f"  Chunk #{i+1}: {total_rows:,} rows processed "
                  f"({rate:,.0f} rows/sec)")

    elapsed = time.time() - t0
    print(f"  Done. {total_rows:,} rows in {elapsed:.1f}s "
          f"({total_rows/elapsed:,.0f} rows/sec)")

    # ---- Phase 2: Output JSON ----
    print("\n[Phase 2] Building and writing JSON files...")
    t0 = time.time()

    seasons = sorted(acc.league.keys())
    print(f"  Seasons found: {len(seasons)} ({', '.join(seasons)})")

    for season in seasons:
        data = acc.build_season_json(season)
        filename = f"hexbin_season_{season.replace('/', '-')}.json"
        filepath = OUTPUT_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        league_count = len(data["league"]["hexbins"])
        team_count = len(data["teams"])
        player_count = len(data["players"])
        fsize = filepath.stat().st_size / 1024
        print(f"  {filename}: {fsize:.0f} KB | "
              f"league={league_count} cells, "
              f"teams={team_count}, players={player_count}")

    elapsed = time.time() - t0
    print(f"  Done. {len(seasons)} files written in {elapsed:.1f}s")

    # ---- Phase 3: Validate ----
    print("\n[Phase 3] Validating output...")
    validate_output(OUTPUT_DIR, len(seasons))

    # Summary
    total_size = sum(
        fp.stat().st_size for fp in OUTPUT_DIR.glob("hexbin_season_*.json")
    )
    print(f"\n{'=' * 60}")
    print(f"All done! {len(seasons)} season files, {total_size / (1024*1024):.1f} MB total")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
