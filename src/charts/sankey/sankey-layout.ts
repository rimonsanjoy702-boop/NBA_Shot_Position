/**
 * sankey-layout.ts — Node positioning + SVG flow ribbon generation.
 *
 * Fixed 4-column layout:
 *   L1 (time)   x=60     8 nodes
 *   L2 (zone)   x=380    7 nodes
 *   L3 (action) x=720    5 nodes
 *   L4 (result) x=1060   2 nodes
 *
 * Link ribbons: each link is a filled polygon whose top/bottom edges are
 * cubic beziers. At the source (right edge), the ribbon's vertical span is
 * proportional to link.value / total_outgoing(source). At the target (left
 * edge), the span is proportional to link.value / total_incoming(target).
 * This makes flows "bundle" to fill node heights exactly.
 */

import type {
  SankeyNode,
  SankeyLink,
  SankeyNodeLayout,
  SankeyLinkLayout,
} from './types'

// ============================================================================
// Constants
// ============================================================================

export const SVG_WIDTH = 1200
export const SVG_HEIGHT = 820
const V_PADDING = 40
const USABLE_H = SVG_HEIGHT - 2 * V_PADDING
const COL_X = [60, 380, 720, 1060]
const COL_W = [100, 120, 120, 90]
const NODE_GAP = 6

// Horizontal curvature factor for bezier control points
const CURVE = 0.35

// ============================================================================
// Node layout
// ============================================================================

export function layoutNodes(nodes: SankeyNode[]): SankeyNodeLayout[] {
  const byLayer: Record<number, SankeyNode[]> = { 1: [], 2: [], 3: [], 4: [] }
  for (const n of nodes) {
    if (byLayer[n.layer]) byLayer[n.layer].push(n)
  }

  const result: SankeyNodeLayout[] = []

  for (const layer of [1, 2, 3, 4]) {
    const layerNodes = byLayer[layer]
    if (layerNodes.length === 0) continue

    const totalSize = layerNodes.reduce((sum, n) => sum + n.size, 0)
    if (totalSize === 0) continue

    const totalGaps = (layerNodes.length - 1) * NODE_GAP
    const availableH = USABLE_H - totalGaps

    // Sort: L1 by time_index, L2 by ZONE_ORDER, L3 by ACTION_ORDER, L4 Made then Missed
    const ZONE_ORDER = ['L2_RA','L2_Paint','L2_MR','L2_LC3','L2_RC3','L2_AB3','L2_BC']
    const ACTION_ORDER = ['L3_Dunk','L3_Layup','L3_Jump','L3_Hook','L3_Tip']

    layerNodes.sort((a, b) => {
      if (a.layer === 1 && a.meta?.time_index !== undefined) {
        return (a.meta.time_index ?? 0) - (b.meta.time_index ?? 0)
      }
      if (a.layer === 2) {
        return ZONE_ORDER.indexOf(a.id) - ZONE_ORDER.indexOf(b.id)
      }
      if (a.layer === 3) {
        return ACTION_ORDER.indexOf(a.id) - ACTION_ORDER.indexOf(b.id)
      }
      if (a.layer === 4) {
        return a.id === 'L4_Made' ? -1 : 1
      }
      return 0
    })

    // Minimum node height: must fit 2 lines of text (~28px) + padding
    const MIN_NODE_HEIGHT = 32

    let y = V_PADDING
    for (const node of layerNodes) {
      const proportional = (node.size / totalSize) * availableH
      const height = Math.max(proportional, MIN_NODE_HEIGHT)
      result.push({ ...node, x: COL_X[layer - 1], y, height })
      y += height + NODE_GAP
    }
  }

  return result
}

// ============================================================================
// Link ribbon path — filled polygon between source and target
// ============================================================================

/**
 * Build a closed SVG path for one flow ribbon.
 *
 *   sy0 ──── bezier ──── ty0   (top edge)
 *   sy1 ──── bezier ◄──── ty1   (bottom edge)
 *
 * The top bezier goes source→target, the bottom bezier goes target→source,
 * with the same curvature so the ribbon looks symmetric.
 */
function ribbonPath(
  // Source exit points (right edge of source node)
  sx: number,
  sy0: number,  // top
  sy1: number,  // bottom
  // Target entry points (left edge of target node)
  tx: number,
  ty0: number,  // top
  ty1: number,  // bottom
): string {
  const dx = Math.abs(tx - sx) * CURVE

  // Top bezier: sx→tx  (left to right)
  // Bottom bezier: tx→sx  (right to left, read backwards = tx→ty1 back to sx→sy1)

  // claude-ignore — use template literals for SVG path readability
  const d = [
    `M ${sx} ${sy0}`,
    `C ${sx + dx} ${sy0}, ${tx - dx} ${ty0}, ${tx} ${ty0}`,  // top edge →
    `L ${tx} ${ty1}`,
    `C ${tx - dx} ${ty1}, ${sx + dx} ${sy1}, ${sx} ${sy1}`,  // bottom edge ←
    `Z`,
  ].join(' ')

  return d
}

// ============================================================================
// Full layout — nodes + flow ribbons
// ============================================================================

export function computeLayout(
  rawNodes: SankeyNode[],
  rawLinks: SankeyLink[],
): {
  positionedNodes: SankeyNodeLayout[]
  positionedLinks: SankeyLinkLayout[]
} {
  // 1. Position nodes
  const nodeMap = new Map<string, SankeyNodeLayout>()
  const positionedNodes = layoutNodes(rawNodes)
  for (const n of positionedNodes) {
    nodeMap.set(n.id, n)
  }

  // 2. Merge links by (source, target) pair — sum values
  const merged: Record<string, { source: string; target: string; value: number }> = {}
  for (const link of rawLinks) {
    const key = `${link.source}::${link.target}`
    if (merged[key]) {
      merged[key].value += link.value
    } else {
      merged[key] = { source: link.source, target: link.target, value: link.value }
    }
  }
  const mergedLinks = Object.values(merged)

  // 3. Precompute total outgoing / incoming per node (from merged links)
  const totalOut: Record<string, number> = {}
  const totalIn: Record<string, number> = {}
  for (const link of mergedLinks) {
    totalOut[link.source] = (totalOut[link.source] || 0) + link.value
    totalIn[link.target]  = (totalIn[link.target]  || 0) + link.value
  }

  // 4. Track cumulative offsets per node for stacking ribbons
  const outOffset: Record<string, number> = {}
  const inOffset: Record<string, number> = {}

  const positionedLinks: SankeyLinkLayout[] = []

  for (const link of mergedLinks) {
    const srcNode = nodeMap.get(link.source)
    const tgtNode = nodeMap.get(link.target)
    if (!srcNode || !tgtNode) continue

    // Vertical span on source
    const srcFraction = totalOut[link.source] > 0
      ? link.value / totalOut[link.source]
      : 0
    const srcY0 = srcNode.y + srcNode.height * (outOffset[link.source] || 0)
    const srcY1 = srcY0 + srcNode.height * srcFraction
    outOffset[link.source] = (outOffset[link.source] || 0) + srcFraction

    // Vertical span on target
    const tgtFraction = totalIn[link.target] > 0
      ? link.value / totalIn[link.target]
      : 0
    const tgtY0 = tgtNode.y + tgtNode.height * (inOffset[link.target] || 0)
    const tgtY1 = tgtY0 + tgtNode.height * tgtFraction
    inOffset[link.target] = (inOffset[link.target] || 0) + tgtFraction

    const sx = srcNode.x + COL_W[srcNode.layer - 1]
    const tx = tgtNode.x

    const path = ribbonPath(sx, srcY0, srcY1, tx, tgtY0, tgtY1)

    // Color from source node's layer
    let color: string
    if (srcNode.layer === 1) {
      color = '#F28E6B'
    } else if (srcNode.layer === 2) {
      color = srcNode.meta?.color || '#199E70'
    } else {
      color = '#7567B2'
    }

    positionedLinks.push({
      source: srcNode,
      target: tgtNode,
      value: link.value,
      path,
      color,
      width: 0,
      opacity: 'full',
    })
  }

  return { positionedNodes, positionedLinks }
}

// ============================================================================
// Helpers for interaction
// ============================================================================

export function getColumnX(layer: number): number {
  return COL_X[layer - 1] ?? 0
}

export function getColumnWidth(layer: number): number {
  return COL_W[layer - 1] ?? 100
}

export function getDownstreamIds(
  nodeId: string,
  links: SankeyLinkLayout[],
): Set<string> {
  const ids = new Set<string>()
  for (const l of links) {
    if (l.source.id === nodeId) ids.add(l.target.id)
  }
  return ids
}

export function getUpstreamIds(
  nodeId: string,
  links: SankeyLinkLayout[],
): Set<string> {
  const ids = new Set<string>()
  for (const l of links) {
    if (l.target.id === nodeId) ids.add(l.source.id)
  }
  return ids
}
