#!/usr/bin/env python3
"""
Patch season_group_agg.json to add 2020-21 ~ 2022-23 win%-only entries
for each group (leader / mid / laggard).

These seasons have no shot data — only standing-derived win_pct.
"""

import json, sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGG_JSON = PROJECT_ROOT / "public" / "data" / "three_point_compare" / "season_group_agg.json"
CLASSIFY_JSON = PROJECT_ROOT / "public" / "data" / "three_point_compare" / "group_classify.json"
STANDINGS_CSV = PROJECT_ROOT / "Data_Source" / "nba_team_standings.csv"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load current data
with open(AGG_JSON, "r", encoding="utf-8") as f:
    agg = json.load(f)

with open(CLASSIFY_JSON, "r", encoding="utf-8") as f:
    classify = json.load(f)

team_group = {t["team_id"]: t["group_type"] for t in classify}

# Load standings for 2020-21 ~ 2022-23
standings = pd.read_csv(STANDINGS_CSV)
standings = standings[standings["season"].between("2020-21", "2022-23")]
standings = standings[standings["team_id"].isin(team_group)]
standings["group_type"] = standings["team_id"].map(team_group)

for season in sorted(standings["season"].unique()):
    sdf = standings[standings["season"] == season]
    entry = {"season": season}
    for gtype in ["leader", "laggard", "mid"]:
        grp = sdf[sdf["group_type"] == gtype]
        if len(grp) == 0:
            continue
        entry[gtype] = {
            "avg_3pa": None,       # no shot data
            "avg_3par": None,      # no shot data
            "avg_win_pct": round(float(grp["win_pct"].mean()), 4),
            "team_cnt": int(len(grp)),
        }
    agg[season] = entry
    print(f"{season}: leader={entry.get('leader',{}).get('avg_win_pct','?')}  "
          f"mid={entry.get('mid',{}).get('avg_win_pct','?')}  "
          f"laggard={entry.get('laggard',{}).get('avg_win_pct','?')}")

with open(AGG_JSON, "w", encoding="utf-8") as f:
    json.dump(agg, f, ensure_ascii=False, indent=2)

all_seasons = sorted(agg.keys())
print(f"\nDone. {len(all_seasons)} seasons: {all_seasons[0]} ~ {all_seasons[-1]}")
for g in ["leader", "mid", "laggard"]:
    wpct_count = sum(1 for s in all_seasons if s in agg and agg[s].get(g) and agg[s][g].get("avg_win_pct") is not None)
    print(f"  {g}: win_pct available in {wpct_count}/{len(all_seasons)} seasons")
