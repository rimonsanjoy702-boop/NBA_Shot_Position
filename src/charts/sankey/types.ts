// ============================================================================
// Sankey chart types
// ============================================================================

/** Single node in the sankey diagram */
export interface SankeyNode {
  id: string           // "L1_0", "L2_RA", "L3_Dunk", "L4_Made" ...
  layer: 1 | 2 | 3 | 4
  label: string        // "Q1前", "Restricted Area", "Dunk", "Made"
  size: number         // total shot count for this node
  meta: {
    fg_pct?: number    // L2 only: field goal percentage
    color?: string     // L2 only: zone color (e.g. "#c9381a")
    time_index?: number // L1 only: 0-7
  }
}

/** Decoded link between two nodes */
export interface SankeyLink {
  source: string       // source node id
  target: string       // target node id
  value: number        // shot count flowing through this link
}

/** Raw link as stored in JSON: [sourceId, targetId, value] */
export type RawSankeyLink = [string, string, number]

/** L2 field goal percentage map: zoneKey → fg_pct */
export type L2FgPctMap = Record<string, number>

/** Entity data block (teams/players): links only, no nodes */
export interface SankeyEntityBlock {
  links: RawSankeyLink[]
  l2_fg_pct: L2FgPctMap
}

/** League data block: full nodes + links */
export interface SankeyLeagueBlock {
  nodes: SankeyNode[]
  links: RawSankeyLink[]
}

/** Court side label (for Hexbin linkage only, data is identical) */
export type CourtSide = 'left' | 'right'

/** Granularity scope */
export type Scope = 'league' | 'team' | 'player'

/** Entity metadata (team or player) */
export interface TeamMeta {
  team_name: string
  abbr: string
  links: RawSankeyLink[]
  l2_fg_pct: L2FgPctMap
}

export interface PlayerMeta {
  player_name: string
  team_id: number
  team_abbr: string
  links: RawSankeyLink[]
  l2_fg_pct: L2FgPctMap
}

/** Full season JSON structure */
export interface SankeySeasonData {
  season: string
  league: SankeyLeagueBlock
  teams: Record<string, TeamMeta>
  players: Record<string, PlayerMeta>
}

/** Selection state for one half-court */
export interface SankeySelection {
  scope: Scope
  entityId?: number
  season: string
}

/** Node with computed vertical position for rendering */
export interface SankeyNodeLayout extends SankeyNode {
  x: number
  y: number
  height: number
}

/** Link with computed path for rendering */
export interface SankeyLinkLayout {
  source: SankeyNodeLayout
  target: SankeyNodeLayout
  value: number
  path: string        // SVG path d-attribute
  color: string       // inherited from L2 zone color
  width: number       // stroke width proportional to value
  opacity: 'full' | 'dimmed'
}

/** Three view states */
export type LoadingState = 'loading' | 'ready' | 'empty' | 'error'

/** All 23 NBA seasons */
export const ALL_SEASONS = [
  '1997-98', '1998-99', '1999-00', '2000-01', '2001-02', '2002-03',
  '2003-04', '2004-05', '2005-06', '2006-07', '2007-08', '2008-09',
  '2009-10', '2010-11', '2011-12', '2012-13', '2013-14', '2014-15',
  '2015-16', '2016-17', '2017-18', '2018-19', '2019-20',
]

/** L2 zone colors (constant, never changes) */
export const ZONE_COLORS: Record<string, string> = {
  'RA': '#c9381a',
  'Paint': '#e8733a',
  'MR': '#f9c74f',
  'LC3': '#72b8a0',
  'RC3': '#55a38a',
  'AB3': '#43aa8b',
  'BC': '#aab3bf',
}

/** All node IDs in canonical order */
export const ALL_NODE_IDS = [
  // L1 (8)
  'L1_0', 'L1_1', 'L1_2', 'L1_3', 'L1_4', 'L1_5', 'L1_6', 'L1_7',
  // L2 (7)
  'L2_RA', 'L2_Paint', 'L2_MR', 'L2_LC3', 'L2_RC3', 'L2_AB3', 'L2_BC',
  // L3 (5)
  'L3_Dunk', 'L3_Layup', 'L3_Jump', 'L3_Hook', 'L3_Tip',
  // L4 (2)
  'L4_Made', 'L4_Missed',
]
