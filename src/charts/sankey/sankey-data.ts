/**
 * sankey-data.ts — Data loading, decoding, and entity node reconstruction.
 *
 * JSON format (v5 optimized):
 *   league.{side}  → { nodes: SankeyNode[], links: RawSankeyLink[] }
 *   teams.{tid}.{side}  → { links: RawSankeyLink[], l2_fg_pct: {...} }
 *   players.{pid}.{side} → { links: RawSankeyLink[], l2_fg_pct: {...} }
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
  SankeyLeagueBlock,
  SankeyEntityBlock,
  CourtSide,
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
 *
 * Logic:
 *   - Clone league template nodes (id, label, layer, color)
 *   - Derive sizes: sum link values flowing through each node
 *   - Override L2 fg_pct from entity's own l2_fg_pct map
 *   - Filter out nodes with size=0
 */
export function reconstructEntityNodes(
  leagueNodes: SankeyNode[],
  decodedLinks: SankeyLink[],
  l2FgPct: Record<string, number>,
): SankeyNode[] {
  // Compute node sizes from links
  const sizeMap: Record<string, number> = {}

  for (const link of decodedLinks) {
    // L1→L2: source=L1, target=L2
    if (link.source.startsWith('L1_')) {
      sizeMap[link.source] = (sizeMap[link.source] || 0) + link.value
      sizeMap[link.target] = (sizeMap[link.target] || 0) + link.value
    }
    // L2→L3: source=L2, target=L3 — L2 already counted above
    else if (link.source.startsWith('L2_')) {
      // L2 size already from L1→L2 links; take max to be safe
      sizeMap[link.source] = Math.max(sizeMap[link.source] || 0, link.value)
      sizeMap[link.target] = (sizeMap[link.target] || 0) + link.value
    }
    // L3→L4: source=L3, target=L4 — L3 already counted above
    else if (link.source.startsWith('L3_')) {
      sizeMap[link.target] = (sizeMap[link.target] || 0) + link.value
    }
  }

  // Build nodes from league template
  const nodes: SankeyNode[] = []
  for (const template of leagueNodes) {
    const size = sizeMap[template.id] || 0
    if (size === 0) continue // entity has no data for this node

    const node: SankeyNode = {
      ...template,
      size,
      meta: { ...template.meta },
    }

    // Override L2 fg_pct
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
// 4. Main extractor — returns ready-to-render { nodes, links }
// ---------------------------------------------------------------------------

export interface SankeyRenderData {
  nodes: SankeyNode[]
  links: SankeyLink[]
}

/**
 * Extract sankey data for a given scope/entity/court-side.
 * This is the single entry point for the chart component.
 */
export function extractSankeyData(
  data: SankeySeasonData,
  scope: Scope,
  courtSide: CourtSide,
  entityId?: number,
): SankeyRenderData {
  // League: direct read (nodes + links)
  if (scope === 'league') {
    const block: SankeyLeagueBlock = data.league[courtSide]
    return {
      nodes: block.nodes,
      links: decodeLinks(block.links),
    }
  }

  // Team
  if (scope === 'team' && entityId != null) {
    const teamData = data.teams[String(entityId)]
    if (!teamData) return { nodes: [], links: [] }
    const block: SankeyEntityBlock = teamData[courtSide]
    const decodedLinks = decodeLinks(block.links)
    return {
      nodes: reconstructEntityNodes(data.league[courtSide].nodes, decodedLinks, block.l2_fg_pct),
      links: decodedLinks,
    }
  }

  // Player
  if (scope === 'player' && entityId != null) {
    const playerData = data.players[String(entityId)]
    if (!playerData) return { nodes: [], links: [] }
    const block: SankeyEntityBlock = playerData[courtSide]
    const decodedLinks = decodeLinks(block.links)
    return {
      nodes: reconstructEntityNodes(data.league[courtSide].nodes, decodedLinks, block.l2_fg_pct),
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

/** Get all teams available in this season */
export function getAvailableTeams(data: SankeySeasonData): EntityOption[] {
  return Object.entries(data.teams).map(([id, info]) => ({
    id: Number(id),
    name: `${info.team_name} (${info.abbr})`,
  }))
}

/** Get all players available in this season */
export function getAvailablePlayers(data: SankeySeasonData): EntityOption[] {
  return Object.entries(data.players).map(([id, info]) => ({
    id: Number(id),
    name: info.player_name,
  }))
}
