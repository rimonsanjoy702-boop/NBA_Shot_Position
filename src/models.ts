export type MediaPlatform = 'weibo' | 'twitter' | 'rednote';

export const mediaPlatforms = ['weibo', 'twitter', 'rednote'] as MediaPlatform[];

export type AccountInterest =
    'animals' |
    'arts and culture' |
    'business and finance' |
    'entertainment' |
    'fashion and beauty' |
    'fitness and health' |
    'food and dining' |
    'learning and educational' |
    'politics' |
    'science and technology' |
    'sports' |
    'travel'

export const accountInterests = ['animals', 'arts and culture', 'business and finance', 'entertainment', 'fashion and beauty', 'fitness and health', 'food and dining', 'learning and educational', 'politics', 'science and technology', 'sports', 'travel'] as AccountInterest[];

export type AccountRole = 'inactive' | 'information-seeker' | 'information-source' | 'general';

export const accountRoles = ['inactive', 'information-seeker', 'information-source', 'general'] as AccountRole[];


export type AccountNodePK = ({
  type: 'role'
  key: AccountRole
} | {
  type: 'platform'
  key: MediaPlatform
} | {
  type: 'interest'
  key: AccountInterest
})

export type AccountStatsNode =
    AccountNodePK & {
  id: string
  size: number
}

export type AccountStatsLink = {
  node1: string
  node2: string
  size: number
}

// ============================================================================
// Hexbin types (appended for NBA shot chart feature)
// ============================================================================

/** Hexbin cell — one hexagon in the grid */
export interface HexbinCell {
  x: number;
  y: number;
  count: number;
  fg_pct: number;
}

/** Per-entity hexbin data with optional time bins */
export interface HexbinEntityData {
  hexbins: HexbinCell[];
  hexbins_by_time: Record<string, HexbinCell[]>;
}

/** Team entry in season JSON */
export interface HexbinTeamEntry extends HexbinEntityData {
  team_name: string;
  abbr: string;
}

/** Player entry in season JSON */
export interface HexbinPlayerEntry extends HexbinEntityData {
  player_name: string;
  team_id: number;
  team_abbr: string;
}

/** Full season JSON structure */
export interface HexbinSeasonData {
  season: string;
  league: HexbinEntityData;
  teams: Record<string, HexbinTeamEntry>;
  players: Record<string, HexbinPlayerEntry>;
}

/** Selection state for one half-court */
export interface HalfCourtSelection {
  scope: 'league' | 'team' | 'player';
  entityId?: number;
  season: string;
  entityLabel?: string;
}

/** Time bin definition */
export const TIME_BIN_LABELS: Record<number, string> = {
  0: 'Q1 前段',
  1: 'Q1 后段',
  2: 'Q2 前段',
  3: 'Q2 后段',
  4: 'Q3 前段',
  5: 'Q3 后段',
  6: 'Q4 前段',
  7: 'Q4 后段',
};

/** All 23 NBA seasons */
export const ALL_SEASONS = [
  '1997-98', '1998-99', '1999-00', '2000-01', '2001-02', '2002-03',
  '2003-04', '2004-05', '2005-06', '2006-07', '2007-08', '2008-09',
  '2009-10', '2010-11', '2011-12', '2012-13', '2013-14', '2014-15',
  '2015-16', '2016-17', '2017-18', '2018-19', '2019-20',
];
