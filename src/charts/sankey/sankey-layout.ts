/**
 * sankey-layout.ts — Node positioning + SVG path generation.
 *
 * Fixed 4-column layout:
 *   L1 (time)  x=0     8 nodes
 *   L2 (zone)  x=350   7 nodes
 *   L3 (action) x=700  5 nodes
 *   L4 (result) x=1050 2 nodes
 *
 * Within each column, node heights and y-positions are proportional to `size`.
 * Link paths use cubic bezier curves from source right-edge to target left-edge.
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

/** SVG viewBox dimensions */
export const SVG_WIDTH = 1200
export const SVG_HEIGHT = 820
/** Padding at top and bottom */
const V_PADDING = 40
/** Usable height for node columns */
const USABLE_H = SVG_HEIGHT - 2 * V_PADDING
/** Column X positions */
const COL_X = [60, 380, 720, 1060]
/** Column widths (for node rectangles) */
const COL_W = [100, 120, 120, 90]
/** Gap between nodes in the same column */
const NODE_GAP = 6

// ============================================================================
// Node layout
// ============================================================================

/**
 * Compute (x, y, height) for every node.
 *
 * Strategy: within each layer, distribute nodes vertically proportional to
 * their size, with small gaps. The total node area + gaps fills USABLE_H.
 */
export function layoutNodes(nodes: SankeyNode[]): SankeyNodeLayout[] {
  // Group nodes by layer
  const byLayer: Record<number, SankeyNode[]> = { 1: [], 2: [], 3: [], 4: [] }
  for (const n of nodes) {
    if (byLayer[n.layer]) {
      byLayer[n.layer].push(n)
    }
  }

  const result: SankeyNodeLayout[] = []

  for (const layer of [1, 2, 3, 4]) {
    const layerNodes = byLayer[layer]
    if (layerNodes.length === 0) continue

    const totalSize = layerNodes.reduce((sum, n) => sum + n.size, 0)
    if (totalSize === 0) continue

    const totalGaps = (layerNodes.length - 1) * NODE_GAP
    const availableH = USABLE_H - totalGaps

    // Sort nodes by a stable order
    // L1: by time_index; L2: by zone order (hardcoded in data); L3: by data order; L4: Made then Missed
    layerNodes.sort((a, b) => {
      if (a.meta?.time_index !== undefined && b.meta?.time_index !== undefined) {
        return a.meta.time_index - b.meta.time_index
      }
      if (a.layer === 4) {
        return a.id === 'L4_Made' ? -1 : 1
      }
      return 0
    })

    let y = V_PADDING
    for (const node of layerNodes) {
      const height = Math.max((node.size / totalSize) * availableH, 4) // min 4px

      result.push({
        ...node,
        x: COL_X[layer - 1],
        y,
        height,
      })

      y += height + NODE_GAP
    }
  }

  return result
}

// ============================================================================
// Link path generation
// ============================================================================

/**
 * Generate SVG cubic bezier path for a sankey link.
 *
 * Curve starts at the right edge of the source node, ends at the left edge
 * of the target node, with horizontal control point offsets.
 */
export function makeLinkPath(
  source: SankeyNodeLayout,
  target: SankeyNodeLayout,
): string {
  // Source exit point (right edge, vertical center)
  const sx = source.x + COL_W[source.layer - 1]
  const sy = source.y + source.height / 2

  // Target entry point (left edge, vertical center)
  const tx = target.x
  const ty = target.y + target.height / 2

  // Horizontal offset for control points (curvature)
  const dx = Math.abs(tx - sx) * 0.4

  const cx1 = sx + dx
  const cy1 = sy
  const cx2 = tx - dx
  const cy2 = ty

  return `M ${sx} ${sy} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${tx} ${ty}`
}

// ============================================================================
// Full layout — nodes + links
// ============================================================================

/**
 * Input: raw nodes + links
 * Output: fully-laid-out nodes + links with SVG paths, colors, widths.
 */
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

  // 2. Compute link properties
  const positionedLinks: SankeyLinkLayout[] = []

  // Compute max link value for width scaling
  const maxValue = rawLinks.reduce((m, l) => Math.max(m, l.value), 0)

  for (const link of rawLinks) {
    const srcNode = nodeMap.get(link.source)
    const tgtNode = nodeMap.get(link.target)
    if (!srcNode || !tgtNode) continue

    // Color: inherit from L2 zone color
    // For L1→L2 links: target is L2
    // For L2→L3 links: source is L2
    // For L3→L4 links: trace back to the L2 source via the current link's source
    let color: string
    if (srcNode.layer === 2) {
      color = srcNode.meta?.color || '#e0e0e0'
    } else if (tgtNode.layer === 2) {
      color = tgtNode.meta?.color || '#e0e0e0'
    } else {
      // L3→L4: no zone color → use a neutral gray
      color = '#a0a8b0'
    }

    // Width: proportional to value, min 1px, max 40px
    const width = maxValue > 0
      ? Math.max(1, (link.value / maxValue) * 40)
      : 1

    const path = makeLinkPath(srcNode, tgtNode)

    positionedLinks.push({
      source: srcNode,
      target: tgtNode,
      value: link.value,
      path,
      color,
      width,
      opacity: 'full',
    })
  }

  return { positionedNodes, positionedLinks }
}

// ============================================================================
// Helpers for interaction
// ============================================================================

/**
 * Get column X for a layer. Layers 1-4 map to [0,1,2,3].
 */
export function getColumnX(layer: number): number {
  return COL_X[layer - 1] ?? 0
}

/** Get column width for a layer */
export function getColumnWidth(layer: number): number {
  return COL_W[layer - 1] ?? 100
}

/**
 * Compute downstream node IDs: given a node ID, return all
 * nodes reachable via links from it (1 hop).
 */
export function getDownstreamIds(
  nodeId: string,
  links: SankeyLinkLayout[],
): Set<string> {
  const ids = new Set<string>()
  for (const l of links) {
    if (l.source.id === nodeId) {
      ids.add(l.target.id)
    }
  }
  return ids
}

/**
 * Compute upstream node IDs: given a node ID, return all
 * nodes that have links pointing to it.
 */
export function getUpstreamIds(
  nodeId: string,
  links: SankeyLinkLayout[],
): Set<string> {
  const ids = new Set<string>()
  for (const l of links) {
    if (l.target.id === nodeId) {
      ids.add(l.source.id)
    }
  }
  return ids
}
