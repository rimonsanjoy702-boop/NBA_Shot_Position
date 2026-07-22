#!/usr/bin/env python3
"""
NBA Sankey Data Preprocessing Script (v2 — optimized)
======================================================
根据《NBA四层桑基投篮结构图设计》§6（v5）规范：
- league: 存 nodes + links（完整模板）
- teams/players: 仅存 links + l2_fg_pct（前端从 league 模板重建 nodes）

输出: public/data/sankey/sankey_season_{YYYY-YY}.json (共23份，紧凑格式)

用法:
    python scripts/build_sankey_data.py

依赖: pandas >= 1.5
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHOT_CSV = PROJECT_ROOT / "Data_Source" / "NBA Shot Locations 1997 - 2020.csv"
OUTPUT_DIR = PROJECT_ROOT / "public" / "data" / "sankey"

MIN_COUNT_LEAGUE = 5
MIN_COUNT_TEAM   = 5
MIN_COUNT_PLAYER = 3

# ============================================================================
# Helpers
# ============================================================================

def derive_season(game_date: int) -> str:
    year = game_date // 10000
    month = (game_date // 100) % 100
    return f"{year}-{str(year+1)[2:]}" if month >= 10 else f"{year-1}-{str(year)[2:]}"


TIME_BIN_LABELS = ["Q1前","Q1后","Q2前","Q2后","Q3前","Q3后","Q4前","Q4后"]

def compute_time_bin(period: int, minutes_remaining: int) -> int | None:
    if period > 4:
        return None
    return (period - 1) * 2 + (1 if minutes_remaining < 6 else 0)


ZONE_MAP = {
    "Restricted Area": "RA", "In The Paint (Non-RA)": "Paint",
    "Mid-Range": "MR", "Left Corner 3": "LC3", "Right Corner 3": "RC3",
    "Above the Break 3": "AB3", "Backcourt": "BC",
}
ZONE_LABELS = {
    "RA":"Restricted Area","Paint":"Paint (Non-RA)","MR":"Mid-Range",
    "LC3":"Left Corner 3","RC3":"Right Corner 3","AB3":"Above the Break 3","BC":"Backcourt",
}
ZONE_COLORS = {
    "RA":"#c9381a","Paint":"#e8733a","MR":"#f9c74f",
    "LC3":"#72b8a0","RC3":"#55a38a","AB3":"#43aa8b","BC":"#aab3bf",
}
ZONE_ORDER = ["RA","Paint","MR","LC3","RC3","AB3","BC"]

ACTION_LABELS = {"Dunk":"Dunk","Layup":"Layup","Jump":"Jump Shot","Hook":"Hook Shot","Tip":"Tip-In"}
ACTION_ORDER = ["Dunk","Layup","Jump","Hook","Tip"]


def classify_action_type(action_type: str) -> str:
    at = str(action_type).lower()
    if "dunk" in at or "slam" in at:       return "Dunk"
    if "hook" in at:                        return "Hook"
    if "tip" in at or "putback" in at:      return "Tip"
    if "layup" in at or "finger roll" in at: return "Layup"
    return "Jump"


def court_side(x: int) -> str:
    return "right" if x > 0 else "left"


# ============================================================================
# Team name / abbr map
# ============================================================================

ABBR_MAP = {
    "Atlanta Hawks":"ATL","Boston Celtics":"BOS","Brooklyn Nets":"BKN","New Jersey Nets":"NJN",
    "Charlotte Hornets":"CHA","Charlotte Bobcats":"CHA","Chicago Bulls":"CHI",
    "Cleveland Cavaliers":"CLE","Dallas Mavericks":"DAL","Denver Nuggets":"DEN",
    "Detroit Pistons":"DET","Golden State Warriors":"GSW","Houston Rockets":"HOU",
    "Indiana Pacers":"IND","Los Angeles Clippers":"LAC","LA Clippers":"LAC",
    "Los Angeles Lakers":"LAL","Memphis Grizzlies":"MEM","Vancouver Grizzlies":"VAN",
    "Miami Heat":"MIA","Milwaukee Bucks":"MIL","Minnesota Timberwolves":"MIN",
    "New Orleans Pelicans":"NOP","New Orleans Hornets":"NOH",
    "New Orleans/Oklahoma City Hornets":"NOK","New York Knicks":"NYK",
    "Oklahoma City Thunder":"OKC","Seattle SuperSonics":"SEA","Orlando Magic":"ORL",
    "Philadelphia 76ers":"PHI","Phoenix Suns":"PHX","Portland Trail Blazers":"POR",
    "Sacramento Kings":"SAC","San Antonio Spurs":"SAS","Toronto Raptors":"TOR",
    "Utah Jazz":"UTA","Washington Wizards":"WAS",
}


def collect_team_names() -> tuple[dict[int,str], dict[int,str]]:
    """Quick CSV pass: team_id → (team_name, abbr)."""
    print("=" * 60)
    print("[Phase 0] Collecting team name mappings ...")
    print("=" * 60)
    names: dict[int,str] = {}
    abbrs: dict[int,str] = {}
    for chunk in pd.read_csv(SHOT_CSV, chunksize=200_000, usecols=["Team ID","Team Name"]):
        for _, row in chunk.iterrows():
            tid = int(row["Team ID"])
            tn = str(row["Team Name"])
            names[tid] = tn
            abbrs[tid] = ABBR_MAP.get(tn, tn[:3].upper())
    print(f"  {len(names)} teams mapped")
    return names, abbrs


# ============================================================================
# Build logic — league (full: nodes + links)
# ============================================================================

def build_league_data(agg: dict, min_count: int) -> dict:
    """
    agg: (tb, zone, action, outcome) → count
    Returns {"nodes": [...], "links": [...]}
    """
    l1_size: dict[int,int] = defaultdict(int)
    l2_size: dict[str,int] = defaultdict(int)
    l2_made: dict[str,int] = defaultdict(int)
    l3_size: dict[str,int] = defaultdict(int)
    l4_size: dict[str,int] = defaultdict(int)
    links: list[dict] = []

    for (tb, zone, action, outcome), cnt in agg.items():
        if cnt < min_count:
            continue
        links.append([f"L1_{tb}",   f"L2_{zone}",   cnt])
        links.append([f"L2_{zone}",  f"L3_{action}", cnt])
        links.append([f"L3_{action}",f"L4_{outcome}", cnt])
        l1_size[tb] += cnt
        l2_size[zone] += cnt
        l3_size[action] += cnt
        l4_size[outcome] += cnt
        if outcome == "Made":
            l2_made[zone] += cnt

    nodes = []
    for tb in range(8):
        if l1_size.get(tb, 0) > 0:
            nodes.append({"id":f"L1_{tb}","layer":1,"label":TIME_BIN_LABELS[tb],"size":l1_size[tb],"meta":{"time_index":tb}})
    for z in ZONE_ORDER:
        if l2_size.get(z, 0) > 0:
            t = l2_size[z]; m = l2_made.get(z, 0)
            nodes.append({"id":f"L2_{z}","layer":2,"label":ZONE_LABELS[z],"size":t,"meta":{"fg_pct":round(m/t,3) if t>0 else 0,"color":ZONE_COLORS[z]}})
    for a in ACTION_ORDER:
        if l3_size.get(a, 0) > 0:
            nodes.append({"id":f"L3_{a}","layer":3,"label":ACTION_LABELS[a],"size":l3_size[a],"meta":{}})
    for o in ["Made","Missed"]:
        if l4_size.get(o, 0) > 0:
            nodes.append({"id":f"L4_{o}","layer":4,"label":o,"size":l4_size[o],"meta":{}})
    return {"nodes": nodes, "links": links}


# ============================================================================
# Build logic — entity (optimized: links + l2_fg_pct only, no nodes)
# ============================================================================

def build_entity_data(agg: dict, min_count: int) -> dict:
    """
    agg: (tb, zone, action, outcome) → count
    Returns {"links": [...], "l2_fg_pct": {...}}
    """
    l2_total: dict[str,int] = defaultdict(int)
    l2_made: dict[str,int] = defaultdict(int)
    links: list[dict] = []

    for (tb, zone, action, outcome), cnt in agg.items():
        if cnt < min_count:
            continue
        # Backcourt: keep at ≥1
        if zone == "BC" and cnt < 1:
            continue
        links.append([f"L1_{tb}",   f"L2_{zone}",   cnt])
        links.append([f"L2_{zone}",  f"L3_{action}", cnt])
        links.append([f"L3_{action}",f"L4_{outcome}", cnt])
        l2_total[zone] += cnt
        if outcome == "Made":
            l2_made[zone] += cnt

    l2_fg_pct = {}
    for z in ZONE_ORDER:
        t = l2_total.get(z, 0)
        if t > 0:
            l2_fg_pct[z] = round(l2_made.get(z, 0) / t, 3)
        # if t==0, omit this zone from the map (entity has no shots in this zone)

    return {"links": links, "l2_fg_pct": l2_fg_pct}


# ============================================================================
# Phase 1: Read CSV & aggregate
# ============================================================================

def build_aggregates():
    """Returns (league_agg, team_agg, player_agg, player_meta)."""
    print("=" * 60)
    print("[Phase 1] Reading CSV & aggregating ...")
    print(f"  Source: {SHOT_CSV}")
    print("=" * 60)

    league: dict[tuple,int] = defaultdict(int)
    team:   dict[tuple,int] = defaultdict(int)
    player: dict[tuple,int] = defaultdict(int)
    player_meta: dict[int,dict] = {}

    total_rows = 0; kept_rows = 0; n_chunks = 0

    for chunk in pd.read_csv(SHOT_CSV, chunksize=200_000):
        n_chunks += 1; total_rows += len(chunk)
        chunk = chunk[chunk["Season Type"] == "Regular Season"]
        if len(chunk) == 0:
            continue

        for _, row in chunk.iterrows():
            tb = compute_time_bin(int(row["Period"]), int(row["Minutes Remaining"]))
            if tb is None: continue
            season = derive_season(int(row["Game Date"]))
            zone = ZONE_MAP.get(str(row["Shot Zone Basic"]))
            if zone is None: continue
            action = classify_action_type(str(row["Action Type"]))
            outcome = "Made" if int(row["Shot Made Flag"])==1 else "Missed"
            side = court_side(int(row["X Location"]))
            tid = int(row["Team ID"])
            pid = int(row["Player ID"])
            pname = str(row["Player Name"])

            league[(season, side, tb, zone, action, outcome)] += 1
            team[(season, tid, side, tb, zone, action, outcome)] += 1
            player[(season, pid, side, tb, zone, action, outcome)] += 1
            if pid not in player_meta:
                player_meta[pid] = {"name": pname, "team_id": tid}
            else:
                player_meta[pid]["name"] = pname
                player_meta[pid]["team_id"] = tid
            kept_rows += 1

        if n_chunks % 5 == 0:
            print(f"  Chunk #{n_chunks}: {total_rows:,} rows, {kept_rows:,} kept")

    print(f"  Done. {total_rows:,} total, {kept_rows:,} kept")
    print(f"  League keys: {len(league):,}  Team keys: {len(team):,}  Player keys: {len(player):,}  Players: {len(player_meta):,}")
    return league, team, player, player_meta


# ============================================================================
# Phase 2: Build per-season JSON
# ============================================================================

def build_season_outputs(league_agg, team_agg, player_agg, player_meta,
                         team_names: dict, team_abbrs: dict):
    print("\n" + "=" * 60)
    print("[Phase 2] Building per-season JSON ...")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_seasons = sorted({s for (s,*_) in league_agg})
    print(f"  Seasons: {all_seasons[0]} ~ {all_seasons[-1]} ({len(all_seasons)} total)")

    total_mb = 0.0
    errors = []

    for season in all_seasons:
        print(f"\n  [{season}]", end=" ", flush=True)

        # --- League (full: nodes + links) ---
        league_data = {}
        for side in ["all","left","right"]:
            side_agg = defaultdict(int)
            for (s, sd, tb, zone, action, outcome), cnt in league_agg.items():
                if s==season and (side=="all" or sd==side):
                    side_agg[(tb, zone, action, outcome)] += cnt
            league_data[side] = build_league_data(side_agg, MIN_COUNT_LEAGUE)

        season_json = {"season": season, "league": league_data, "teams": {}, "players": {}}

        # --- Teams (optimized: links + l2_fg_pct only) ---
        season_teams = set()
        for (s, tid, *_) in team_agg:
            if s == season: season_teams.add(tid)

        for tid in sorted(season_teams):
            team_data = {}
            for side in ["all","left","right"]:
                side_agg = defaultdict(int)
                for (s, t, sd, tb, zone, action, outcome), cnt in team_agg.items():
                    if s==season and t==tid and (side=="all" or sd==side):
                        side_agg[(tb, zone, action, outcome)] += cnt
                team_data[side] = build_entity_data(side_agg, MIN_COUNT_TEAM)
            season_json["teams"][str(tid)] = {
                "team_name": team_names.get(tid, f"Team {tid}"),
                "abbr": team_abbrs.get(tid, ""),
                **team_data,
            }

        # --- Players (optimized: links + l2_fg_pct only) ---
        season_players = set()
        for (s, pid, *_) in player_agg:
            if s == season: season_players.add(pid)

        for pid in sorted(season_players):
            meta = player_meta.get(pid, {})
            player_data = {}
            total_shots = 0
            for side in ["all","left","right"]:
                side_agg = defaultdict(int)
                for (s, p, sd, tb, zone, action, outcome), cnt in player_agg.items():
                    if s==season and p==pid and (side=="all" or sd==side):
                        side_agg[(tb, zone, action, outcome)] += cnt
                        if side == "all":
                            total_shots += cnt
                player_data[side] = build_entity_data(side_agg, MIN_COUNT_PLAYER)
            if total_shots < MIN_COUNT_PLAYER:
                continue
            season_json["players"][str(pid)] = {
                "player_name": meta.get("name", f"Player {pid}"),
                "team_id": meta.get("team_id", 0),
                "team_abbr": team_abbrs.get(meta.get("team_id", 0), ""),
                **player_data,
            }

        # --- Write (compact JSON) ---
        filename = f"sankey_season_{season}.json"
        filepath = OUTPUT_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(season_json, f, ensure_ascii=False, separators=(",", ":"))
        size_kb = filepath.stat().st_size / 1024
        total_mb += size_kb / 1024

        n_t = len(season_json["teams"])
        n_p = len(season_json["players"])
        print(f"→ {filename}  {size_kb:.0f} KB  (teams={n_t}, players={n_p})")

    print(f"\n  Total: {len(all_seasons)} files, {total_mb:.1f} MB")

    # --- Validation ---
    print("\n" + "=" * 60)
    print("[Validation]")
    print("=" * 60)
    if len(all_seasons) != 23:
        errors.append(f"Expected 23 seasons, got {len(all_seasons)}")
    if total_mb > 15:
        errors.append(f"Total size {total_mb:.1f} MB exceeds 15 MB limit")
    if errors:
        print(f"  FAILED ({len(errors)} issues):")
        for e in errors: print(f"    ✗ {e}")
    else:
        print(f"  PASSED — {total_mb:.1f} MB total, under 15 MB budget")
    return errors


# ============================================================================
# Main
# ============================================================================

def main():
    t0 = time.time()
    print("=" * 60)
    print("NBA Four-Layer Sankey — Data Preprocessing (v2 optimized)")
    print("=" * 60)

    team_names, team_abbrs = collect_team_names()
    league_agg, team_agg, player_agg, player_meta = build_aggregates()
    errors = build_season_outputs(league_agg, team_agg, player_agg, player_meta,
                                   team_names, team_abbrs)

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"Done! ({elapsed:.1f}s)")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
