import type { HexbinSeasonData, HexbinCell } from '@/models';

const DATA_BASE_URL = import.meta.env.BASE_URL + 'data/';

/** Fetch one season's hexbin JSON from public/data/ */
export async function fetchHexbinSeason(season: string): Promise<HexbinSeasonData> {
  const filename = `hexbin_season_${season}.json`;
  const resp = await fetch(DATA_BASE_URL + filename);
  if (!resp.ok) {
    throw new Error(`Failed to fetch ${filename}: ${resp.status}`);
  }
  return (await resp.json()) as HexbinSeasonData;
}

/** Extract hexbin cells for a specific scope from season data */
export function extractHexbins(
  data: HexbinSeasonData,
  scope: 'league' | 'team' | 'player',
  entityId?: number,
  timeBin?: number | null,
): HexbinCell[] {
  if (scope === 'league') {
    if (timeBin != null) {
      return data.league.hexbins_by_time[String(timeBin)] ?? [];
    }
    return data.league.hexbins;
  }

  if (scope === 'team' && entityId != null) {
    const teamData = data.teams[String(entityId)];
    if (!teamData) return [];
    if (timeBin != null) {
      return teamData.hexbins_by_time[String(timeBin)] ?? [];
    }
    return teamData.hexbins;
  }

  if (scope === 'player' && entityId != null) {
    const playerData = data.players[String(entityId)];
    if (!playerData) return [];
    if (timeBin != null) {
      return playerData.hexbins_by_time[String(timeBin)] ?? [];
    }
    return playerData.hexbins;
  }

  return [];
}

/** Get available teams from season data */
export function getAvailableTeams(data: HexbinSeasonData): { id: number; name: string; abbr: string }[] {
  return Object.entries(data.teams).map(([id, info]) => ({
    id: Number(id),
    name: info.team_name,
    abbr: info.abbr,
  }));
}

/** Get available players from season data */
export function getAvailablePlayers(data: HexbinSeasonData): { id: number; name: string }[] {
  return Object.entries(data.players).map(([id, info]) => ({
    id: Number(id),
    name: info.player_name,
  }));
}

/** All 23 NBA seasons available */
export const ALL_SEASONS = [
  '1997-98', '1998-99', '1999-00', '2000-01', '2001-02', '2002-03',
  '2003-04', '2004-05', '2005-06', '2006-07', '2007-08', '2008-09',
  '2009-10', '2010-11', '2011-12', '2012-13', '2013-14', '2014-15',
  '2015-16', '2016-17', '2017-18', '2018-19', '2019-20',
];
