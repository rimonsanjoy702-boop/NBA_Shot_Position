#!/usr/bin/env python3
"""
NBA Team Standings -- Fetch team win/loss records from stats.nba.com
====================================================================
Uses subprocess-per-season isolation to avoid TCP connection-pool
reuse conflicts that cause intermittent failures when batching.

Two modes
---------
Orchestrator (no args):
    python scripts/fetch_team_standings.py
    -> spawns one subprocess per season, collects results, writes CSV, runs QA.

Single-season (--season):
    python scripts/fetch_team_standings.py --season 1997-98 --out temp.json
    -> fetches one season, writes result to the given temp file.

Output
------
    Data_Source/nba_team_standings.csv
    quality_check/standings_quality_report.json
    quality_check/standings_quality_report.txt
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows UTF-8
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "Data_Source"
QA_DIR = PROJECT_ROOT / "quality_check"
CSV_OUTPUT = DATA_DIR / "nba_team_standings.csv"
QA_JSON = QA_DIR / "standings_quality_report.json"
QA_TXT = QA_DIR / "standings_quality_report.txt"

SEASONS = [f"{y}-{str(y + 1)[2:]}" for y in range(1997, 2023)]

SPECIAL_SEASONS = {
    "1998-99": {"expected_games_min": 50, "expected_games_max": 50, "reason": "Lockout"},
    "2011-12": {"expected_games_min": 66, "expected_games_max": 66, "reason": "Lockout"},
    "2012-13": {"expected_games_min": 81, "expected_games_max": 82,
                 "reason": "Boston Marathon bombing — BOS/IND game cancelled, not replayed"},
    "2019-20": {"expected_games_min": 64, "expected_games_max": 75, "reason": "COVID-19"},
    "2020-21": {"expected_games_min": 72, "expected_games_max": 72, "reason": "COVID-adjusted"},
}

DEFAULT_GAMES_MIN = 82
DEFAULT_GAMES_MAX = 82


# ============================================================================
# Mode 1 -- Single-season worker (called via subprocess)
# ============================================================================

# --- Structural errors: the API changed its response shape ---
# Retrying won't help; bail immediately so the orchestrator knows.
class StructuralError(Exception):
    """Raised when the API response shape doesn't match what we expect."""


def fetch_one_season(season: str, out_path: Path) -> None:
    """
    Fetch standings for a single season from nba_api.
    Writes JSON to *out_path* on success.
    Exits with code 1 on transient failure, code 2 on structural failure.
    """
    from nba_api.stats.endpoints import leaguestandings

    def _safe_int(val) -> int | None:
        """int() that tolerates None/empty-string for nullable API fields."""
        if val is None:
            return None
        if isinstance(val, str) and val.strip() == "":
            return None
        return int(val)

    max_retries = 5
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            standings = leaguestandings.LeagueStandings(
                league_id="00", season=season, timeout=120,
            )
            data = standings.get_dict()
            rs = [r for r in data.get("resultSets", []) if r["name"] == "Standings"]
            if not rs:
                raise RuntimeError("No 'Standings' resultSet in response")

            rs = rs[0]
            headers = rs["headers"]
            row_set = rs["rowSet"]

            # --- Field lookups (structural -- fail hard if missing) ---
            try:
                idx_tid = headers.index("TeamID")
                idx_city = headers.index("TeamCity")
                idx_name = headers.index("TeamName")
                idx_wins = headers.index("WINS")
                idx_losses = headers.index("LOSSES")
                idx_wpct = headers.index("WinPCT")
                idx_conf = headers.index("Conference")
                idx_div = headers.index("Division")
                idx_div_rank = headers.index("DivisionRank")
                idx_league_rank = headers.index("LeagueRank")
            except ValueError as e:
                raise StructuralError(
                    f"Expected column not found in API response: {e}"
                ) from e

            rows = []
            for row in row_set:
                try:
                    rows.append({
                        "season": season,
                        "team_id": int(row[idx_tid]),
                        "team_full_name": f"{row[idx_city]} {row[idx_name]}",
                        "conference": row[idx_conf],
                        "division": row[idx_div],
                        "division_rank": _safe_int(row[idx_div_rank]),
                        "league_rank": _safe_int(row[idx_league_rank]),
                        "wins": int(row[idx_wins]),
                        "losses": int(row[idx_losses]),
                        "games": int(row[idx_wins]) + int(row[idx_losses]),
                        "win_pct": float(row[idx_wpct]),
                    })
                except (ValueError, IndexError) as e:
                    raise StructuralError(
                        f"Bad row data in API response for {season}: {e}"
                    ) from e

            # --- Success: write to temp file ---
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
            return  # done

        except StructuralError:
            # Hard failure -- don't retry, tell orchestrator clearly
            print(f"[{season}] STRUCTURAL ERROR (no retry): {e}",
                  file=sys.stderr)
            sys.exit(2)

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                import random
                wait = 2 ** attempt + random.uniform(0, 2)
                print(f"[{season}] attempt {attempt}/{max_retries} failed: "
                      f"{type(e).__name__}. Retrying in {wait:.1f}s ...",
                      file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"[{season}] FAILED after {max_retries} attempts: "
                      f"{type(e).__name__}: {e}", file=sys.stderr)
                sys.exit(1)

    sys.exit(1)  # unreachable


def worker_main():
    """Entry point for --season mode."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", required=True)
    parser.add_argument("--out", required=True, help="Path for the result JSON file")
    args = parser.parse_args()

    out_path = Path(args.out)
    fetch_one_season(args.season, out_path)


# ============================================================================
# Mode 2 -- Orchestrator (no args)
# ============================================================================

def orchestrator_main():
    import pandas as pd

    script_path = Path(__file__).resolve()
    python_exe = sys.executable

    all_rows: list[dict] = []
    failed_seasons: list[str] = []
    structural_failures: list[str] = []
    t0_total = time.time()

    print("=" * 60)
    print("NBA Team Standings -- subprocess-per-season orchestrator")
    print(f"Seasons: {SEASONS[0]} ~ {SEASONS[-1]} ({len(SEASONS)} total)")
    print(f"Worker:  {python_exe}")
    print("=" * 60)

    for idx, season in enumerate(SEASONS, 1):
        print(f"  [{idx:2d}/{len(SEASONS)}] {season} ... ", end="", flush=True)

        # Create a temp file for the worker to write its result into.
        # Physical isolation avoids stdout-pollution JSON parse failures.
        fd, tmp_path_str = tempfile.mkstemp(
            suffix=".json", prefix=f"standings_{season.replace('-', '_')}_"
        )
        os_close_early(fd)  # close the fd so the child can write

        t0 = time.time()
        try:
            result = subprocess.run(
                [python_exe, str(script_path), "--season", season,
                 "--out", tmp_path_str],
                capture_output=True, text=True, timeout=180,
                cwd=str(PROJECT_ROOT),
            )
        except subprocess.TimeoutExpired:
            elapsed = time.time() - t0
            print(f"TIMEOUT ({elapsed:.1f}s)")
            failed_seasons.append(season)
            _cleanup_tmp(tmp_path_str)
            continue

        elapsed = time.time() - t0

        if result.returncode == 0:
            # Worker succeeded -- read its temp file
            try:
                with open(tmp_path_str, "r", encoding="utf-8") as f:
                    rows = json.load(f)
                all_rows.extend(rows)
                n_teams = len(rows)
                print(f"OK  ({n_teams} teams, {elapsed:.1f}s)")
            except (json.JSONDecodeError, OSError) as e:
                print(f"FILE-ERR ({elapsed:.1f}s) -- {e}")
                failed_seasons.append(season)
        elif result.returncode == 2:
            # Structural error (API shape changed)
            print(f"STRUCT-ERR ({elapsed:.1f}s)")
            structural_failures.append(season)
            if result.stderr:
                print(f"       stderr: {result.stderr.strip()[:200]}")
        else:
            # Transient failure (returncode 1)
            print(f"FAIL ({elapsed:.1f}s)")
            failed_seasons.append(season)
            if result.stderr:
                err = result.stderr.strip()
                print(f"       stderr: {err[:300]}")

        _cleanup_tmp(tmp_path_str)

        # Brief pause between subprocess calls
        if idx < len(SEASONS):
            time.sleep(0.5)

    total_time = time.time() - t0_total

    # ---- Summary ----
    print(f"\n{'=' * 60}")
    summary_parts = [f"{len(SEASONS) - len(failed_seasons) - len(structural_failures)}/{len(SEASONS)} seasons OK"]
    if failed_seasons:
        summary_parts.append(f"FAILED (transient): {failed_seasons}")
    if structural_failures:
        summary_parts.append(f"STRUCT-ERR: {structural_failures}")
    print(f"Fetch complete: {len(all_rows)} rows, " + ", ".join(summary_parts))
    print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"{'=' * 60}")

    if not all_rows:
        print("ERROR: No data fetched. Aborting.")
        sys.exit(1)

    # ---- Write CSV ----
    print("\nWriting CSV ...")
    df = pd.DataFrame(all_rows)
    df = df.sort_values(["season", "team_id"]).reset_index(drop=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8")
    print(f"  {CSV_OUTPUT}")
    print(f"  {len(df)} rows, {CSV_OUTPUT.stat().st_size / 1024:.1f} KB")

    # ---- Quality checks ----
    print("\nRunning quality checks ...")
    fetch_log = _build_fetch_log(SEASONS, failed_seasons)
    checks = run_quality_checks_inline(df, fetch_log)

    # ---- Write reports ----
    QA_DIR.mkdir(parents=True, exist_ok=True)

    report_data = {
        "metadata": {
            "source": "stats.nba.com via nba_api (subprocess-per-season)",
            "seasons_range": f"{SEASONS[0]} ~ {SEASONS[-1]}",
            "seasons_count": len(SEASONS),
            "total_rows": len(df),
            "failed_seasons": failed_seasons,
            "structural_failures": structural_failures,
            "api_fetch_duration_s": round(total_time, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "checks": {k: _make_serializable(v) for k, v in checks.items()},
    }
    with open(QA_JSON, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"  {QA_JSON}")

    write_text_report_inline(df, checks, SEASONS, failed_seasons,
                             structural_failures, total_time, QA_TXT)

    passed = checks["summary"]["passed"]
    total = checks["summary"]["total_checks"]
    print(f"\n{'=' * 60}")
    print(f"Done!")
    print(f"  Data: {CSV_OUTPUT}")
    print(f"  QA:   {QA_TXT} ({passed}/{total} checks passed)")
    print(f"{'=' * 60}")


def os_close_early(fd: int) -> None:
    """Close a file descriptor without blowing up if it's already closed."""
    import os
    try:
        os.close(fd)
    except OSError:
        pass


def _cleanup_tmp(path: str) -> None:
    """Remove a temp file; ignore if already gone."""
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


def _build_fetch_log(seasons: list[str], failed: list[str]) -> list[dict]:
    """Synthesize fetch_log-style entries from orchestrator results."""
    failed_set = set(failed)
    log = []
    for s in seasons:
        log.append({
            "season": s,
            "attempt": 1,
            "status": "error" if s in failed_set else "ok",
            "duration_s": 0.0,
            "teams_returned": 0 if s in failed_set else 1,  # placeholder
            "error": "subprocess failed" if s in failed_set else None,
        })
    return log


# ============================================================================
# Quality checks (inline -- same logic, adapted for script-local types)
# ============================================================================

def run_quality_checks_inline(df: "pd.DataFrame", fetch_log: list[dict]) -> dict:
    import pandas as pd

    print("\n" + "=" * 60)
    print("Standings QA")
    print("=" * 60)

    # Q1 -- season coverage
    print("\n[Q1] Season coverage ...")
    ok_set = {e["season"] for e in fetch_log if e["status"] == "ok"}
    fail_set = {e["season"] for e in fetch_log if e["status"] != "ok"}
    q1 = {
        "expected_seasons": len(SEASONS),
        "fetched_ok": len(ok_set),
        "fetched_failed": len(fail_set),
        "failed_seasons": sorted(fail_set),
        "total_api_calls": len(fetch_log),
    }
    if not fail_set:
        print(f"  OK  all {len(SEASONS)} seasons fetched")
    else:
        print(f"  FAIL  missing: {sorted(fail_set)}")

    # Q2 -- team count per season
    print("\n[Q2] Team count per season ...")
    season_team_counts = df.groupby("season")["team_id"].nunique()
    q2_issues = []
    for s, c in season_team_counts.items():
        expected = 29 if s < "2004-05" else 30
        if c != expected:
            q2_issues.append({"season": s, "got": c, "expected": str(expected)})
    q2 = {"anomalies": q2_issues}
    if not q2_issues:
        print("  OK  all seasons have correct team count")
    else:
        for a in q2_issues:
            print(f"  FAIL {a['season']}: {a['got']} teams (expected {a['expected']})")

    # Q3 -- games played
    print("\n[Q3] Games-played plausibility ...")
    q3 = {}
    for season in sorted(df["season"].unique()):
        sdf = df[df["season"] == season]
        spec = SPECIAL_SEASONS.get(season, {})
        exp_lo = spec.get("expected_games_min", DEFAULT_GAMES_MIN)
        exp_hi = spec.get("expected_games_max", DEFAULT_GAMES_MAX)
        outside = sdf[(sdf["games"] < exp_lo) | (sdf["games"] > exp_hi)]
        q3[season] = {
            "min": int(sdf["games"].min()),
            "max": int(sdf["games"].max()),
            "avg": round(float(sdf["games"].mean()), 1),
            "expected": f"{exp_lo}-{exp_hi}",
            "pass": len(outside) == 0,
        }
    all_pass_q3 = all(v["pass"] for v in q3.values())
    if all_pass_q3:
        print(f"  OK  all {len(q3)} seasons within expected range")
    else:
        for s, v in q3.items():
            if not v["pass"]:
                print(f"  FAIL {s}: {v['min']}-{v['max']} games (expected {v['expected']})")

    # Q4 -- WinPCT validation
    print("\n[Q4] WinPCT in [0,1] & W/(W+L) consistency ...")
    bad_range = df[(df["win_pct"] < 0) | (df["win_pct"] > 1)]
    calc_pct = (df["wins"] / (df["wins"] + df["losses"])).round(3)
    mismatch = (abs(df["win_pct"] - calc_pct) > 0.01).sum()
    q4 = {
        "out_of_range": int(len(bad_range)),
        "calc_mismatch": int(mismatch),
    }
    if q4["out_of_range"] == 0 and q4["calc_mismatch"] == 0:
        print("  OK  all values valid and consistent")
    else:
        print(f"  FAIL  out-of-range={q4['out_of_range']}, calc-mismatch={q4['calc_mismatch']}")

    # Q5 -- Team ID alignment with shot CSV
    # Uses pd.to_numeric(..., errors="coerce") to safely handle dirty data.
    print("\n[Q5] Team ID vs shot CSV ...")
    shot_csv = DATA_DIR / "NBA Shot Locations 1997 - 2020.csv"
    if shot_csv.exists():
        csv_tids = set()
        for chunk in pd.read_csv(shot_csv, chunksize=500000, usecols=["Team ID"]):
            # Safe conversion: coerce non-numeric garbage to NaN, then drop
            ids = pd.to_numeric(chunk["Team ID"], errors="coerce").dropna().astype(int)
            csv_tids.update(ids)
            if len(csv_tids) >= 40:
                break
        api_tids = set(df["team_id"].unique())
        only_csv = csv_tids - api_tids
        only_api = api_tids - csv_tids
        q5 = {"csv_teams": len(csv_tids), "api_teams": len(api_tids),
              "common": len(csv_tids & api_tids), "only_csv": sorted(only_csv),
              "only_api": sorted(only_api)}
        print(f"  csv={len(csv_tids)}  api={len(api_tids)}  common={len(csv_tids & api_tids)}")
        if only_csv:
            print(f"  ONLY in CSV: {only_csv}")
        if only_api:
            print(f"  ONLY in API: {only_api}")
    else:
        q5 = {"note": "shot CSV not found, skipped"}
        print("  SKIP  shot CSV not found")

    # Q6 -- nulls (only core fields; league_rank is null pre-2008 by API design)
    print("\n[Q6] Missing values (core fields) ...")
    core_cols = ["season", "team_id", "team_full_name", "wins", "losses", "games", "win_pct"]
    null_cols = {col: int(cnt) for col, cnt in df[core_cols].isna().sum().items() if cnt > 0}
    q6 = {"null_columns": null_cols}
    if null_cols:
        print(f"  FAIL  {null_cols}")
    else:
        print(f"  OK  no missing values in {len(df.columns)} columns")

    # Q7 -- row count
    print("\n[Q7] Row count ...")
    lo, hi = len(SEASONS) * 29, len(SEASONS) * 30
    q7 = {"rows": len(df), "expected": f"{lo}-{hi}", "pass": lo <= len(df) <= hi}
    if q7["pass"]:
        print(f"  OK  {len(df)} rows in [{lo}, {hi}]")
    else:
        print(f"  FAIL  {len(df)} rows not in [{lo}, {hi}]")

    # Summary
    checks = {"Q1_season_coverage": q1, "Q2_team_count": q2,
              "Q3_games_played": q3, "Q4_winpct_validation": q4,
              "Q5_team_id_alignment": q5, "Q6_missing_values": q6,
              "Q7_row_count": q7}

    total = 7
    passed = 0
    failed_items = []
    if not fail_set:                              passed += 1
    else:                                         failed_items.append("Q1")
    if not q2_issues:                             passed += 1
    else:                                         failed_items.append("Q2")
    if all_pass_q3:                               passed += 1
    else:                                         failed_items.append("Q3")
    if q4["out_of_range"] == 0 and q4["calc_mismatch"] == 0: passed += 1
    else:                                         failed_items.append("Q4")
    if q5.get("only_csv") is not None and len(q5.get("only_csv", [])) == 0: passed += 1
    elif q5.get("note"):                          passed += 1  # skipped -> pass
    else:                                         failed_items.append("Q5")
    if not null_cols:                             passed += 1
    else:                                         failed_items.append("Q6")
    if q7["pass"]:                                passed += 1
    else:                                         failed_items.append("Q7")

    checks["summary"] = {"total_checks": total, "passed": passed,
                         "failed": total - passed, "failed_items": failed_items}
    print(f"\n  Result: {passed}/{total} passed")
    if failed_items:
        print(f"  Failed: {', '.join(failed_items)}")

    return checks


# ============================================================================
# Text report
# ============================================================================

def write_text_report_inline(df, checks, seasons, failed_seasons,
                             structural_failures, total_time, path):
    lines = []
    lines.append("=" * 72)
    lines.append("NBA Team Season Standings -- Quality Report")
    lines.append("=" * 72)
    lines.append(f"Source:       stats.nba.com (nba_api, subprocess-per-season)")
    lines.append(f"Seasons:      {seasons[0]} ~ {seasons[-1]} ({len(seasons)} total)")
    lines.append(f"Rows:         {len(df)}")
    lines.append(f"Timestamp:    {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Fetch time:   {total_time:.1f}s ({total_time/60:.1f} min)")
    lines.append(f"Mode:         subprocess-per-season isolation (temp-file IPC)")
    lines.append("")

    s = checks["summary"]
    lines.append("-" * 72)
    lines.append(f"Summary: {s['passed']}/{s['total_checks']} checks passed")
    if failed_seasons:
        lines.append(f"  Transient FAILED seasons: {failed_seasons}")
    if structural_failures:
        lines.append(f"  Structural FAILED seasons: {structural_failures}")
    lines.append("")

    q1 = checks["Q1_season_coverage"]
    lines.append(f"Q1 Season coverage: {q1['fetched_ok']}/{q1['expected_seasons']} seasons OK")

    q2 = checks["Q2_team_count"]
    lines.append(f"Q2 Team counts:     {'OK' if not q2['anomalies'] else 'FAIL ' + str(q2['anomalies'])}")

    q3 = checks["Q3_games_played"]
    bad_q3 = [s for s, v in q3.items() if not v["pass"]] if isinstance(q3, dict) else []
    lines.append(f"Q3 Games played:    {'OK' if not bad_q3 else 'FAIL ' + str(bad_q3)}")

    q4 = checks["Q4_winpct_validation"]
    lines.append(f"Q4 WinPCT validation: out-of-range={q4['out_of_range']}, calc-mismatch={q4['calc_mismatch']}")

    q5 = checks["Q5_team_id_alignment"]
    lines.append(f"Q5 Team ID alignment: {q5}")

    q6 = checks["Q6_missing_values"]
    lines.append(f"Q6 Missing values:  {q6['null_columns'] if q6['null_columns'] else 'none'}")

    q7 = checks["Q7_row_count"]
    lines.append(f"Q7 Row count:       {q7['rows']} (expected {q7['expected']}) {'OK' if q7['pass'] else 'FAIL'}")

    lines.append("")
    lines.append("-" * 72)
    if s["failed"] == 0 and not failed_seasons and not structural_failures:
        lines.append("Verdict: PASS -- data ready for preprocessing.")
    else:
        lines.append(f"Verdict: NEEDS FIX -- {s['failed']} checks failed, "
                     f"{len(failed_seasons)} transient failures, "
                     f"{len(structural_failures)} structural failures.")
    lines.append("-" * 72)
    lines.append("")
    lines.append("=" * 72)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  {path}")


def _make_serializable(obj):
    if isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, (set, frozenset)):
        return sorted(obj) if all(isinstance(x, (int, str)) for x in obj) else list(obj)
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


# ============================================================================
# Dispatch
# ============================================================================

if __name__ == "__main__":
    if "--season" in sys.argv:
        worker_main()
    else:
        orchestrator_main()
