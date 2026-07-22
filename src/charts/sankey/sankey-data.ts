/**
 * sankey-data.ts — Data loading, decoding, and entity node reconstruction.
 *
 * JSON format (v6):
 *   league  → { nodes: SankeyNode[], links: RawSankeyLink[] }
 *   teams.{tid}  → { team_name, abbr, links: RawSankeyLink[], l2_fg_pct: {...} }
 *   players.{pid} → { player_name, team_id, team_abbr, links: RawSankeyLink[], l2_fg_pct: {...} }
 *
 * Raw links are arrays [sourceId, targetId, value] in JSON; this module decodes
 * them to SankeyLink objects. Entity nodes are reconstructed from the league
 * template with sizes derived from links and fg_pct from l2_fg_pct.
 */

import type {
  SankeyNode,
  SankeyLink,
  RawSankeyLink,
  SankeySeasonData,
  Scope,
} from './types'

const DATA_BASE = import.meta.env.BASE_URL + 'data/sankey/'

// ---------------------------------------------------------------------------
// 1. Fetch
// ---------------------------------------------------------------------------

/** Fetch one season's sankey JSON */
export async function fetchSankeySeason(season: string): Promise<SankeySeasonData> {
  const url = `${DATA_BASE}sankey_season_${season}.json`
  const resp = await fetch(url)
  if (!resp.ok) {
    throw new Error(`Failed to fetch sankey data for ${season}: HTTP ${resp.status}`)
  }
  return (await resp.json()) as SankeySeasonData
}

// ---------------------------------------------------------------------------
// 2. Decode raw links → SankeyLink objects
// ---------------------------------------------------------------------------

/** Convert raw array links to object links */
export function decodeLinks(raw: RawSankeyLink[]): SankeyLink[] {
  return raw.map(([source, target, value]) => ({ source, target, value }))
}

// ---------------------------------------------------------------------------
// 3. Entity node reconstruction (design doc §6.6)
// ---------------------------------------------------------------------------

/**
 * Reconstruct entity nodes from league template + entity links + l2_fg_pct.
 */
export function reconstructEntityNodes(
  leagueNodes: SankeyNode[],
  decodedLinks: SankeyLink[],
  l2FgPct: Record<string, number>,
): SankeyNode[] {
  const sizeMap: Record<string, number> = {}

  for (const link of decodedLinks) {
    if (link.source.startsWith('L1_')) {
      sizeMap[link.source] = (sizeMap[link.source] || 0) + link.value
      sizeMap[link.target] = (sizeMap[link.target] || 0) + link.value
    } else if (link.source.startsWith('L2_')) {
      sizeMap[link.source] = Math.max(sizeMap[link.source] || 0, link.value)
      sizeMap[link.target] = (sizeMap[link.target] || 0) + link.value
    } else if (link.source.startsWith('L3_')) {
      sizeMap[link.target] = (sizeMap[link.target] || 0) + link.value
    }
  }

  const nodes: SankeyNode[] = []
  for (const template of leagueNodes) {
    const size = sizeMap[template.id] || 0
    if (size === 0) continue

    const node: SankeyNode = { ...template, size, meta: { ...template.meta } }
    if (template.layer === 2) {
      const zoneKey = template.id.replace('L2_', '')
      if (l2FgPct[zoneKey] !== undefined) {
        node.meta = { ...node.meta, fg_pct: l2FgPct[zoneKey] }
      }
    }
    nodes.push(node)
  }
  return nodes
}

// ---------------------------------------------------------------------------
// 4. Main extractor
// ---------------------------------------------------------------------------

export interface SankeyRenderData {
  nodes: SankeyNode[]
  links: SankeyLink[]
}

export function extractSankeyData(
  data: SankeySeasonData,
  scope: Scope,
  entityId?: number,
): SankeyRenderData {
  // League
  if (scope === 'league') {
    return {
      nodes: data.league.nodes,
      links: decodeLinks(data.league.links),
    }
  }

  // Team
  if (scope === 'team' && entityId != null) {
    const teamData = data.teams[String(entityId)]
    if (!teamData) return { nodes: [], links: [] }
    const decodedLinks = decodeLinks(teamData.links)
    return {
      nodes: reconstructEntityNodes(data.league.nodes, decodedLinks, teamData.l2_fg_pct),
      links: decodedLinks,
    }
  }

  // Player
  if (scope === 'player' && entityId != null) {
    const playerData = data.players[String(entityId)]
    if (!playerData) return { nodes: [], links: [] }
    const decodedLinks = decodeLinks(playerData.links)
    return {
      nodes: reconstructEntityNodes(data.league.nodes, decodedLinks, playerData.l2_fg_pct),
      links: decodedLinks,
    }
  }

  return { nodes: [], links: [] }
}

// ---------------------------------------------------------------------------
// 5. Available entities in a season
// ---------------------------------------------------------------------------

export interface EntityOption {
  id: number
  name: string
}

export function getAvailableTeams(data: SankeySeasonData): EntityOption[] {
  return Object.entries(data.teams).map(([id, info]) => ({
    id: Number(id),
    name: `${info.team_name} (${info.abbr})`,
  }))
}

export function getAvailablePlayers(data: SankeySeasonData): EntityOption[] {
  return Object.entries(data.players).map(([id, info]) => ({
    id: Number(id),
    name: info.player_name,
  }))
}
