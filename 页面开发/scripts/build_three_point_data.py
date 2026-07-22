#!/usr/bin/env python3
"""
Three-Point Transition Data Preprocessing Script
=================================================
Reads NBA Shot Locations CSV + team standings CSV, computes per-team-per-season
3P metrics, detects inflection points, classifies teams into leader/laggard/mid
groups, and outputs three JSON files for the D3 frontend chart.

Output: public/data/three_point_compare/
  team_season_3p_raw.json   — per-team per-season detail
  group_classify.json       — 37-team group assignment + turn-point season
  season_group_agg.json     — season × group aggregated means (for line chart)

Usage:
    python scripts/build_three_point_data.py

Dependencies: pandas >= 1.5, numpy >= 1.22
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Windows UTF-8 compatibility
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Inputs
SHOT_CSV = PROJECT_ROOT / "Data_Source" / "NBA Shot Locations 1997 - 2020.csv"
STANDINGS_CSV = PROJECT_ROOT / "Data_Source" / "nba_team_standings.csv"

# Output
OUTPUT_DIR = PROJECT_ROOT / "public" / "data" / "three_point_compare"
RAW_JSON = OUTPUT_DIR / "team_season_3p_raw.json"
CLASSIFY_JSON = OUTPUT_DIR / "group_classify.json"
AGG_JSON = OUTPUT_DIR / "season_group_agg.json"

# Turn-point threshold (absolute level -- GSW 2014-15 benchmark)
TURN_POINT_3PAR = 0.30       # 3-point attempt rate ≥ 30%
TURN_POINT_3PA = 27           # and 3PA per game ≥ 27

# Group boundary seasons (inclusive)
LEADER_SEASONS_MAX = "2014-15"   # first crossing ≤ 2014-15 → leader
MID_SEASONS_MAX = "2017-18"      # first crossing 2015-16 ~ 2017-18 → mid
# Laggard: first crossing ≥ 2018-19

MIN_SEASONS_FOR_TEAM = 5        # teams with fewer seasons excluded

# Teams that moved/rebranded — map historical names to canonical for display
# Keyed by team_id, the canonical name is the most recent one
# We'll infer canonical names from the latest season each team appears in.

# ============================================================================
# Season helpers (reuse same logic as build_hexbin_data.py)
# ============================================================================

def derive_season(game_date: int) -> str:
    """Convert Game Date (YYYYMMDD int) to NBA season label 'YYYY-YY'."""
    year = game_date // 10000
    month = (game_date // 100) % 100
    if month >= 10:
        return f"{year}-{str(year + 1)[2:]}"
    else:
        return f"{year - 1}-{str(year)[2:]}"


# ============================================================================
# Phase 1: Per-team per-season shooting stats from shot CSV
# ============================================================================

def build_team_season_stats() -> pd.DataFrame:
    """
    Read shot CSV in chunks, aggregate per (Team ID, Season).
    Returns DataFrame with columns:
        team_id, season, team_name, total_fga, total_3pa, games_played
    """
    print("=" * 60)
    print("[Phase 1] Aggregating per-team per-season shooting stats ...")
    print(f"  Source: {SHOT_CSV}")
    print("=" * 60)

    # Accumulators: (team_id, season) -> {fga, 3pa, game_ids}
    acc: dict[tuple[int, str], dict] = defaultdict(
        lambda: {"fga": 0, "tpa": 0, "game_ids": set(), "team_name": ""}
    )

    chunk_size = 200_000
    total_rows = 0
    regular_season_rows = 0

    reader = pd.read_csv(SHOT_CSV, chunksize=chunk_size)
    for i, chunk in enumerate(reader):
        total_rows += len(chunk)

        # Regular season only
        chunk = chunk[chunk["Season Type"] == "Regular Season"]
        regular_season_rows += len(chunk)

        if len(chunk) == 0:
            continue

        for _, row in chunk.iterrows():
            tid = int(row["Team ID"])
            gid = int(row["Game ID"])
            gd = int(row["Game Date"])
            season = derive_season(gd)
            shot_type = str(row["Shot Type"])
            team_name = str(row["Team Name"])

            key = (tid, season)
            entry = acc[key]
            entry["fga"] += 1
            if shot_type == "3PT Field Goal":
                entry["tpa"] += 1
            entry["game_ids"].add(gid)
            if not entry["team_name"]:
                entry["team_name"] = team_name
            # Always keep latest (iteration order means last seen = most recent)
            entry["team_name"] = team_name

        if (i + 1) % 5 == 0:
            print(f"  Chunk #{i+1}: {total_rows:,} rows scanned, "
                  f"{len(acc):,} unique (team, season) pairs")

    print(f"  Done. {total_rows:,} rows scanned, {regular_season_rows:,} regular-season, "
          f"{len(acc):,} unique (team, season) pairs")

    # Build DataFrame
    rows = []
    for (tid, season), entry in acc.items():
        games = len(entry["game_ids"])
        if games == 0:
            continue
        rows.append({
            "team_id": tid,
            "season": season,
            "team_name": entry["team_name"],
            "total_fga": entry["fga"],
            "total_3pa": entry["tpa"],
            "games_played": games,
        })

    df = pd.DataFrame(rows)
    # Compute per-game averages
    df["avg_fga"] = (df["total_fga"] / df["games_played"]).round(1)
    df["avg_3pa"] = (df["total_3pa"] / df["games_played"]).round(1)
    df["_3par"] = (df["avg_3pa"] / df["avg_fga"]).round(4)

    print(f"  Output: {len(df)} rows, {df['team_id'].nunique()} teams, "
          f"{df['season'].nunique()} seasons")
    return df


# ============================================================================
# Phase 2: Merge win% from standings CSV
# ============================================================================

def merge_standings(team_stats: pd.DataFrame) -> pd.DataFrame:
    """Left-join standings win_pct onto team-season shooting stats."""
    print("\n" + "=" * 60)
    print("[Phase 2] Merging standings (win%) data ...")
    print(f"  Source: {STANDINGS_CSV}")
    print("=" * 60)

    standings = pd.read_csv(STANDINGS_CSV)
    standings = standings[["season", "team_id", "win_pct", "wins", "losses", "games"]]
    standings = standings.rename(columns={"games": "standing_games"})

    # Track which team_ids are in standings vs shot data
    shot_ids = set(team_stats["team_id"].unique())
    standing_ids = set(standings["team_id"].unique())
    common = shot_ids & standing_ids

    print(f"  Shot CSV teams: {len(shot_ids)}")
    print(f"  Standings teams: {len(standing_ids)}")
    print(f"  Common: {len(common)}")

    only_shot = shot_ids - standing_ids
    only_standings = standing_ids - shot_ids
    if only_shot:
        print(f"  Only in shot CSV: {sorted(only_shot)}")
    if only_standings:
        print(f"  Only in standings: {sorted(only_standings)}")

    merged = team_stats.merge(
        standings,
        on=["team_id", "season"],
        how="left",
    )

    # Use standings games as canonical; fall back to derived games_played
    merged["canonical_games"] = merged["standing_games"].fillna(merged["games_played"]).astype(int)

    no_winpct = merged["win_pct"].isna().sum()
    if no_winpct > 0:
        missing_seasons = merged[merged["win_pct"].isna()][["team_id", "season"]].drop_duplicates()
        print(f"  WARNING: {no_winpct} rows without win_pct "
              f"({len(missing_seasons)} team-seasons)")
        # Fill with NaN — downstream aggregation will skip them
    else:
        print(f"  All {len(merged)} rows have win_pct")

    print(f"  Output: {len(merged)} rows")
    return merged


# ============================================================================
# Phase 3: Inflection-point detection & group classification
# ============================================================================

def detect_inflection_and_classify(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify every team based on the FIRST season it crosses BOTH absolute
    thresholds simultaneously: 3PAr >= 0.30 AND 3PA >= 27.

    This models "three-point transformation" as reaching the GSW 2014-15
    benchmark — a deliberate structural shift to a modern 3P-heavy offense.

    Groups (by first-crossing season):
        leader  – first crossed ≤ 2014-15  (early adopters)
        mid     – first crossed 2015-16 ~ 2017-18
        laggard – first crossed ≥ 2018-19
        never   – still hasn't crossed by end of data (2019-20)

    If a team crossed before 2012-13 (e.g. NYK 2008-09, ORL 2009-10),
    it is still classified as leader — these were genuine early 3P pioneers
    (D'Antoni system, 1-in-4-out spacing) who just happened to be ahead of
    the league-wide wave.
    """
    print("\n" + "=" * 60)
    print("[Phase 3] Classifying teams by absolute threshold ...")
    print(f"  Threshold: 3PAr >= {TURN_POINT_3PAR:.2f}  AND  3PA >= {TURN_POINT_3PA:.0f}")
    print("=" * 60)

    df = df.copy()
    df = df.sort_values(["team_id", "season"]).reset_index(drop=True)

    # Compute deltas (keep them for informational / raw-data output,
    # but the CLASSIFICATION no longer uses them)
    df["delta_3par"] = df.groupby("team_id")["_3par"].diff().round(4)
    df["delta_3pa"] = df.groupby("team_id")["avg_3pa"].diff().round(1)

    df["is_turn_point"] = False
    df["turn_point_reason"] = ""

    group_assignments: dict[int, dict] = {}

    for tid, grp in df.groupby("team_id", sort=True):
        grp = grp.sort_values("season")

        # Find first season where BOTH thresholds are met
        cross_mask = (grp["_3par"] >= TURN_POINT_3PAR) & (grp["avg_3pa"] >= TURN_POINT_3PA)
        cross_rows = grp[cross_mask]

        if len(cross_rows) == 0:
            # Never crossed — note peak for reporting
            peak_3par = grp["_3par"].max()
            peak_3pa = grp["avg_3pa"].max()
            peak_3par_season = grp.loc[grp["_3par"].idxmax(), "season"]
            peak_3pa_season = grp.loc[grp["avg_3pa"].idxmax(), "season"]
            group_assignments[tid] = {
                "turn_point_season": None,
                "group_type": "never",
                "peak_3par": round(peak_3par, 4),
                "peak_3pa": round(peak_3pa, 1),
                "peak_3par_season": peak_3par_season,
                "peak_3pa_season": peak_3pa_season,
            }
            continue

        first = cross_rows.iloc[0]
        turn_season = str(first["season"])

        # Mark the turn-point season
        idx_first = cross_rows.index[0]
        df.at[idx_first, "is_turn_point"] = True
        df.at[idx_first, "turn_point_reason"] = (
            f"3PAr={first['_3par']:.4f} >= {TURN_POINT_3PAR:.2f} AND "
            f"3PA={first['avg_3pa']:.1f} >= {TURN_POINT_3PA:.0f}"
        )

        # Classify by window
        if turn_season <= LEADER_SEASONS_MAX:
            gtype = "leader"
        elif turn_season <= MID_SEASONS_MAX:
            gtype = "mid"
        else:
            gtype = "laggard"

        group_assignments[tid] = {
            "turn_point_season": turn_season,
            "group_type": gtype,
        }

    # Apply group assignments
    df["group_type"] = df["team_id"].map(
        lambda tid: group_assignments.get(tid, {}).get("group_type", "unclassified")
    )
    df["turn_point_season"] = df["team_id"].map(
        lambda tid: group_assignments.get(tid, {}).get("turn_point_season")
    )

    # ---- Filter: exclude teams with < MIN_SEASONS_FOR_TEAM seasons ----
    team_season_counts = df.groupby("team_id")["season"].nunique()
    valid_teams = set(team_season_counts[team_season_counts >= MIN_SEASONS_FOR_TEAM].index)
    excluded = set(team_season_counts[team_season_counts < MIN_SEASONS_FOR_TEAM].index)

    df = df[df["team_id"].isin(valid_teams)].copy()

    # ---- Summary ----
    counts = df.groupby("team_id")["group_type"].first().value_counts()
    for g in ["leader", "mid", "laggard", "never"]:
        if g in counts:
            print(f"  {g.capitalize():<8s}: {int(counts[g]):2d} teams")
    print(f"  Total:     {int(counts.sum())} teams")
    if excluded:
        print(f"  Excluded (< {MIN_SEASONS_FOR_TEAM} seasons): {len(excluded)} teams {sorted(excluded)}")

    # Print detailed group breakdown
    for gtype in ["leader", "mid", "laggard", "never"]:
        teams_in_group = df[df["group_type"] == gtype][["team_id", "team_name", "turn_point_season"]] \
            .drop_duplicates("team_id")
        if len(teams_in_group) == 0:
            continue
        print(f"\n  [{gtype}] ({len(teams_in_group)} teams):")
        for _, t in teams_in_group.iterrows():
            tid_val = int(t["team_id"])
            tp = t["turn_point_season"] if pd.notna(t["turn_point_season"]) else "never"
            name = str(t["team_name"])
            # Show peak for never-crossed teams
            extra = ""
            if gtype == "never":
                ga = group_assignments.get(tid_val, {})
                extra = (f"  peak: 3PA={ga.get('peak_3pa','?')} "
                         f"({ga.get('peak_3pa_season','?')}), "
                         f"3PAr={ga.get('peak_3par','?')}")
            print(f"    {tid_val:>10}  {name:<32s}  1st={tp}{extra}")

    return df


# ============================================================================
# Phase 4: Season × group aggregation
# ============================================================================

def build_season_group_agg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-season per-group means for the line chart.
    """
    print("\n" + "=" * 60)
    print("[Phase 4] Building season × group aggregation ...")
    print("=" * 60)

    # Only aggregate rows that have win_pct
    valid = df[df["win_pct"].notna()].copy()

    agg_rows = []
    for (season, gtype), grp in valid.groupby(["season", "group_type"]):
        agg_rows.append({
            "season": season,
            "group_type": gtype,
            "avg_3pa": round(grp["avg_3pa"].mean(), 2),
            "avg_3par": round(grp["_3par"].mean(), 4),
            "avg_win_pct": round(grp["win_pct"].mean(), 4),
            "team_cnt": int(grp["team_id"].nunique()),
        })

    agg_df = pd.DataFrame(agg_rows)
    agg_df = agg_df.sort_values(["season", "group_type"]).reset_index(drop=True)

    print(f"  {len(agg_df)} rows ({agg_df['season'].nunique()} seasons × "
          f"{agg_df['group_type'].nunique()} groups)")
    print(f"  Seasons: {sorted(agg_df['season'].unique())[0]} ~ "
          f"{sorted(agg_df['season'].unique())[-1]}")
    return agg_df


# ============================================================================
# Phase 5: Output JSON files + validation
# ============================================================================

def write_outputs(team_df: pd.DataFrame, agg_df: pd.DataFrame) -> None:
    """
    Write the three JSON output files and run validation checks.
    """
    print("\n" + "=" * 60)
    print("[Phase 5] Writing output JSON files & validation ...")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- 5a: team_season_3p_raw.json ---
    print("\n  [5a] team_season_3p_raw.json ...")
    raw_list = []
    for tid, grp in team_df.groupby("team_id", sort=True):
        # Get canonical team name (most recent)
        latest = grp.loc[grp["season"].idxmax()]
        team_name = str(latest["team_name"])
        abbr = _team_abbr(team_name)

        seasons = []
        for _, row in grp.sort_values("season").iterrows():
            seasons.append({
                "season": str(row["season"]),
                "total_pa": float(row["avg_fga"]),
                "3pa": float(row["avg_3pa"]),
                "3par": float(row["_3par"]),
                "win_pct": float(row["win_pct"]) if pd.notna(row["win_pct"]) else None,
                "delta_3par": float(row["delta_3par"]) if pd.notna(row["delta_3par"]) else None,
                "delta_3pa": float(row["delta_3pa"]) if pd.notna(row["delta_3pa"]) else None,
                "is_turn_point": bool(row["is_turn_point"]),
                "group_type": str(row["group_type"]),
            })

        raw_list.append({
            "team_id": int(tid),
            "team_name": team_name,
            "abbr": abbr,
            "season_list": seasons,
        })

    with open(RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(raw_list, f, ensure_ascii=False, indent=2)
    print(f"    {RAW_JSON}")
    print(f"    {len(raw_list)} teams, "
          f"{sum(len(t['season_list']) for t in raw_list)} team-seasons")
    fsize_kb = RAW_JSON.stat().st_size / 1024
    print(f"    {fsize_kb:.0f} KB")

    # --- 5b: group_classify.json ---
    print("\n  [5b] group_classify.json ...")
    classify_list = []
    for tid, grp in team_df.groupby("team_id", sort=True):
        latest = grp.loc[grp["season"].idxmax()]
        tp_row = grp[grp["is_turn_point"] == True]
        turn_season = str(tp_row.iloc[0]["season"]) if len(tp_row) > 0 else None
        turn_reason = str(tp_row.iloc[0]["turn_point_reason"]) if len(tp_row) > 0 else None
        gtype = str(grp["group_type"].iloc[0])

        entry = {
            "team_id": int(tid),
            "team_name": str(latest["team_name"]),
            "abbr": _team_abbr(str(latest["team_name"])),
            "group_type": gtype,
            "turn_point_season": turn_season,
            "turn_point_reason": turn_reason,
            "seasons_count": int(grp["season"].nunique()),
        }

        # For "never" teams, include peak values for context
        if gtype == "never":
            entry["peak_3pa"] = grp.loc[grp["avg_3pa"].idxmax(), "avg_3pa"]
            entry["peak_3par"] = grp.loc[grp["_3par"].idxmax(), "_3par"]
            entry["peak_3pa_season"] = grp.loc[grp["avg_3pa"].idxmax(), "season"]

        classify_list.append(entry)

    with open(CLASSIFY_JSON, "w", encoding="utf-8") as f:
        json.dump(classify_list, f, ensure_ascii=False, indent=2)
    print(f"    {CLASSIFY_JSON}")
    print(f"    {len(classify_list)} teams")
    fsize_kb = CLASSIFY_JSON.stat().st_size / 1024
    print(f"    {fsize_kb:.0f} KB")

    # --- 5c: season_group_agg.json ---
    print("\n  [5c] season_group_agg.json ...")
    agg_output = {}
    for season in sorted(agg_df["season"].unique()):
        sdf = agg_df[agg_df["season"] == season]
        entry = {"season": season}
        for gtype in ["leader", "laggard", "mid", "never"]:
            grp = sdf[sdf["group_type"] == gtype]
            if len(grp) > 0:
                r = grp.iloc[0]
                entry[gtype] = {
                    "avg_3pa": float(r["avg_3pa"]),
                    "avg_3par": float(r["avg_3par"]),
                    "avg_win_pct": float(r["avg_win_pct"]),
                    "team_cnt": int(r["team_cnt"]),
                }
        agg_output[season] = entry

    with open(AGG_JSON, "w", encoding="utf-8") as f:
        json.dump(agg_output, f, ensure_ascii=False, indent=2)
    print(f"    {AGG_JSON}")
    print(f"    {len(agg_output)} seasons")
    fsize_kb = AGG_JSON.stat().st_size / 1024
    print(f"    {fsize_kb:.0f} KB")

    # --- Validation ---
    print("\n" + "=" * 60)
    print("[Validation] Running design-doc check-list ...")
    print("=" * 60)

    errors = []

    # V1: 23 seasons, no empty
    n_seasons_agg = agg_df["season"].nunique()
    n_seasons_raw = team_df["season"].nunique()
    print(f"\n  V1: {n_seasons_agg} seasons in agg, {n_seasons_raw} in raw")
    if n_seasons_agg < 23:
        errors.append(f"V1: Only {n_seasons_agg} seasons (expected 23)")

    # V2: 37 teams all classified
    n_teams = team_df["team_id"].nunique()
    unclassified = team_df[team_df["group_type"] == "unclassified"]
    print(f"  V2: {n_teams} teams, {len(unclassified['team_id'].unique())} unclassified")
    if len(unclassified) > 0:
        errors.append(f"V2: {len(unclassified['team_id'].unique())} unclassified teams")

    # V3: 3par, win_pct in [0, 1]
    bad_3par = team_df[(team_df["_3par"] < 0) | (team_df["_3par"] > 1)]
    bad_wpct = team_df[(team_df["win_pct"].notna()) &
                       ((team_df["win_pct"] < 0) | (team_df["win_pct"] > 1))]
    print(f"  V3: 3par out of [0,1]: {len(bad_3par)}, "
          f"win_pct out of [0,1]: {len(bad_wpct)}")
    if len(bad_3par) > 0 or len(bad_wpct) > 0:
        errors.append(f"V3: Values out of range")

    # V4: delta logic — spot check a few teams
    # Pick a known team and verify first delta is NaN, subsequent ones make sense
    sample_team = team_df[team_df["team_id"] == team_df["team_id"].unique()[0]].sort_values("season")
    first_delta_par = sample_team.iloc[0]["delta_3par"]
    print(f"  V4: First delta_3par for team #{sample_team.iloc[0]['team_id']}: "
          f"{first_delta_par} (expected NaN or None)")
    if pd.notna(first_delta_par):
        errors.append("V4: First season delta should be NaN")

    # V5: every team has a group (no "unclassified")
    group_counts = team_df.groupby("team_id")["group_type"].first().value_counts()
    total_classified = group_counts.sum()
    print(f"  V5: {total_classified} teams classified ({dict(group_counts)})")
    unclassified = group_counts.get("unclassified", 0)
    if unclassified > 0:
        errors.append(f"V5: {unclassified} teams unclassified")
        print(f"  V5: {total_classified} teams classified ({dict(group_counts)})")
    else:
        print(f"  V5: All {total_classified} teams classified ({dict(group_counts)})")

    # V6: No duplicate (team_id, season)
    dupes = team_df.duplicated(subset=["team_id", "season"]).sum()
    print(f"  V6: Duplicate (team_id, season) rows: {dupes}")
    if dupes > 0:
        errors.append(f"V6: {dupes} duplicate rows")

    if errors:
        print(f"\n  VALIDATION FAILED ({len(errors)} issues):")
        for e in errors:
            print(f"    ✗ {e}")
    else:
        print(f"\n  VALIDATION PASSED — all checks green")

    return errors


def _team_abbr(full_name: str) -> str:
    """Look up team abbreviation from full name. Falls back to first-3-letters."""
    mapping = {
        "Atlanta Hawks": "ATL",
        "Boston Celtics": "BOS",
        "Brooklyn Nets": "BKN",
        "New Jersey Nets": "NJN",
        "Charlotte Hornets": "CHA",
        "Charlotte Bobcats": "CHA",
        "Chicago Bulls": "CHI",
        "Cleveland Cavaliers": "CLE",
        "Dallas Mavericks": "DAL",
        "Denver Nuggets": "DEN",
        "Detroit Pistons": "DET",
        "Golden State Warriors": "GSW",
        "Houston Rockets": "HOU",
        "Indiana Pacers": "IND",
        "Los Angeles Clippers": "LAC",
        "LA Clippers": "LAC",
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
    return mapping.get(full_name, full_name[:3].upper())


# ============================================================================
# Main
# ============================================================================

def main():
    t0 = time.time()

    print("=" * 60)
    print("NBA Three-Point Transition — Data Preprocessing")
    print(f"Shot CSV:     {SHOT_CSV}")
    print(f"Standings CSV:{STANDINGS_CSV}")
    print(f"Output dir:   {OUTPUT_DIR}")
    print("=" * 60)

    # Phase 1
    team_stats = build_team_season_stats()

    # Phase 2
    merged = merge_standings(team_stats)

    # Phase 3
    classified = detect_inflection_and_classify(merged)

    # Phase 4
    agg = build_season_group_agg(classified)

    # Phase 5
    errors = write_outputs(classified, agg)

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"All done! ({elapsed:.1f}s)")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
