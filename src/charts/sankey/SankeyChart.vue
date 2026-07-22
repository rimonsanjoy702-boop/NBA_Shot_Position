<script setup lang="ts">
/**
 * SankeyChart.vue — Core SVG sankey diagram component.
 *
 * Renders a 4-layer sankey diagram with D3-like layout (hand-rolled).
 * Handles three states: loading, empty, ready. (Error state handled by parent.)
 *
 * Events:
 *   @select-time-bin  — L1 node clicked, emits timeBin index 0-7
 *   @select-zone      — L2 node clicked, emits zone id (e.g. "L2_RA")
 *   @select-action    — L3 node clicked
 *   @select-outcome   — L4 node clicked
 */

import { ref, computed, watch } from 'vue'
import type {
  SankeyNode,
  SankeyLink,
  SankeyNodeLayout,
  SankeyLinkLayout,
  LoadingState,
  SankeySelection,
} from './types'
import { computeLayout } from './sankey-layout'

// ============================================================================
// Props
// ============================================================================

const props = defineProps<{
  /** Current loading/ready/empty state */
  state: LoadingState
  /** Raw nodes (from extractSankeyData) */
  nodes: SankeyNode[]
  /** Raw links (from extractSankeyData) */
  links: SankeyLink[]
  /** Currently selected time bin (-1 = none) */
  selectedTimeBin?: number
  /** Currently selected zone id */
  selectedZone?: string | null
  /** Currently selected action id */
  selectedAction?: string | null
  /** Currently selected outcome id */
  selectedOutcome?: string | null
  /** Title text */
  title?: string
}>()

// ============================================================================
// Emits
// ============================================================================

const emit = defineEmits<{
  'select-time-bin': [index: number]
  'select-zone': [id: string]
  'select-action': [id: string]
  'select-outcome': [id: string]
}>()

// ============================================================================
// Layout computation (reactive)
// ============================================================================

const layout = computed(() => {
  if (!props.nodes.length || !props.links.length) {
    return { positionedNodes: [], positionedLinks: [] }
  }
  return computeLayout(props.nodes, props.links)
})

const positionedNodes = computed(() => layout.value.positionedNodes)
const positionedLinks = computed(() => layout.value.positionedLinks)

// ============================================================================
// Interaction state
// ============================================================================

const hoveredNode = ref<string | null>(null)
const hoveredLink = ref<number | null>(null) // link index

// Compute dimmed links based on selections
const linkOpacity = computed(() => {
  const dimmed = new Set<number>()

  if (props.selectedTimeBin != null && props.selectedTimeBin >= 0) {
    // Only show links connected to the selected L1 node
    const selectedL1Id = `L1_${props.selectedTimeBin}`
    positionedLinks.value.forEach((link, i) => {
      if (link.source.id !== selectedL1Id && link.target.id !== selectedL1Id) {
        dimmed.add(i)
      }
    })
  }

  if (props.selectedZone) {
    positionedLinks.value.forEach((link, i) => {
      if (link.source.id !== props.selectedZone && link.target.id !== props.selectedZone) {
        dimmed.add(i)
      }
    })
  }

  return dimmed
})

// ============================================================================
// Node click handlers
// ============================================================================

function onNodeClick(node: SankeyNodeLayout) {
  if (node.layer === 1 && node.meta?.time_index !== undefined) {
    emit('select-time-bin', node.meta.time_index)
  } else if (node.layer === 2) {
    emit('select-zone', node.id)
  } else if (node.layer === 3) {
    emit('select-action', node.id)
  } else if (node.layer === 4) {
    emit('select-outcome', node.id)
  }
}

// ============================================================================
// Tooltip
// ============================================================================

const tooltip = ref<{
  visible: boolean
  x: number
  y: number
  text: string
}>({ visible: false, x: 0, y: 0, text: '' })

function showTooltip(e: MouseEvent, text: string) {
  const rect = (e.currentTarget as SVGElement).closest('svg')?.getBoundingClientRect()
  if (rect) {
    tooltip.value = {
      visible: true,
      x: e.clientX - rect.left + 12,
      y: e.clientY - rect.top - 8,
      text,
    }
  }
}

function hideTooltip() {
  tooltip.value.visible = false
}

// ============================================================================
// Colors — per-layer ordinal/categorical scheme
//
// L1 (time, 8 nodes):    orange-red ramp — warm, sequential feel (Q1→Q4)
// L2 (zone, 7 nodes):    blue-green ramp — cool, distinct from L1, preserves zone identity
// L3 (action, 5 nodes):  violet-purple ramp — clearly separate from L1 and L2
// L4 (result, 2 nodes):  status green (Made) / status red (Missed)
//
// Each layer has its own distinct hue family; within each layer, darker = later/more
// ============================================================================

/** L1: warm orange-red palette (8 time bins, Q1前 → Q4后 step darker) */
const L1_COLORS = [
  '#F8A47E',  // Q1前 — lightest
  '#F28E6B',  // Q1后
  '#E67A55',  // Q2前
  '#D96942',  // Q2后
  '#C95A34',  // Q3前
  '#B44B27',  // Q3后
  '#9E3E1D',  // Q4前
  '#83341C',  // Q4后 — darkest
]

/** L2: blue-green palette (7 zones, court→perimeter) */
const L2_COLORS: Record<string, string> = {
  'RA':    '#3987E5',  // blue — Restricted Area (paint dominance)
  'Paint': '#5B9BD5',  // lighter blue — Paint (Non-RA)
  'MR':    '#199E70',  // teal-green — Mid-Range
  'LC3':   '#3A9D7A',  // green — Left Corner 3
  'RC3':   '#2D8F6E',  // deeper green — Right Corner 3
  'AB3':   '#1D7A5C',  // darkest green — Above the Break 3
  'BC':    '#6B7D8F',  // slate gray — Backcourt
}

/** L3: violet-purple palette (5 action types) */
const L3_COLORS: Record<string, string> = {
  'Dunk':  '#A398D9',  // light violet — Dunk (explosive)
  'Layup': '#8C81C8',  // medium violet — Layup
  'Jump':  '#7567B2',  // mid violet — Jump Shot
  'Hook':  '#5E5098',  // deeper violet — Hook Shot
  'Tip':   '#4C3F85',  // darkest violet — Tip-In
}

/** L4: status colors */
const L4_MADE_COLOR   = '#22C55E'  // green
const L4_MISSED_COLOR = '#EF4444'  // red

const NODE_STROKE = 'rgba(255,255,255,0.12)'
const NODE_STROKE_HOVER = 'rgba(255,255,255,0.6)'

/** Get node fill color */
function getNodeFill(node: SankeyNode): string {
  if (node.layer === 1) {
    const idx = node.meta?.time_index ?? 0
    if (node.meta?.time_index === props.selectedTimeBin) {
      return '#FFFFFF'  // selected L1: white highlight
    }
    return L1_COLORS[idx] || L1_COLORS[0]
  }
  if (node.layer === 2) {
    const zk = node.id.replace('L2_', '')
    return L2_COLORS[zk] || '#A0A4A8'
  }
  if (node.layer === 3) {
    const ak = node.id.replace('L3_', '')
    return L3_COLORS[ak] || '#A0A4A8'
  }
  if (node.id === 'L4_Made') return L4_MADE_COLOR
  if (node.id === 'L4_Missed') return L4_MISSED_COLOR
  return '#A0A4A8'
}

function getNodeBorderColor(node: SankeyNode): string {
  if (node.layer === 2 && node.meta?.fg_pct !== undefined) {
    const fg = node.meta.fg_pct
    if (fg >= 0.55) return 'rgba(255,255,255,0.5)'
    if (fg >= 0.45) return 'rgba(255,255,255,0.35)'
    if (fg >= 0.35) return 'rgba(255,255,255,0.22)'
    return 'rgba(255,255,255,0.1)'
  }
  return NODE_STROKE
}

function isSelected(node: SankeyNode): boolean {
  if (props.selectedZone === node.id) return true
  if (props.selectedAction === node.id) return true
  if (props.selectedOutcome === node.id) return true
  return false
}

// ============================================================================
// Column headers
// ============================================================================

const COLUMN_HEADERS = [
  { x: 60, label: '场次时间', layer: 1 },
  { x: 380, label: '出手区域', layer: 2 },
  { x: 720, label: '出手方式', layer: 3 },
  { x: 1060, label: '结果', layer: 4 },
]
</script>

<template>
  <div class="sankey-chart">
    <!-- Loading -->
    <div v-if="state === 'loading'" class="state-box">
      <div class="spinner" />
      <p class="state-text">加载投篮结构数据...</p>
    </div>

    <!-- Empty -->
    <div v-else-if="state === 'empty'" class="state-box">
      <span class="state-icon">🏀</span>
      <p class="state-text">暂无投篮结构数据</p>
      <p class="state-detail">该筛选条件下没有足够的数据生成桑基图</p>
    </div>

    <!-- SVG Chart -->
    <svg
      v-else
      class="sankey-svg"
      :viewBox="`0 0 1200 820`"
      preserveAspectRatio="xMidYMid meet"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- Background -->
      <rect x="0" y="0" width="1200" height="820" fill="transparent" />

      <!-- Column headers -->
      <g class="column-headers">
        <text
          v-for="h in COLUMN_HEADERS"
          :key="h.layer"
          :x="h.x"
          y="22"
          text-anchor="middle"
          fill="#8b949e"
          font-size="12"
          font-weight="600"
        >
          {{ h.label }}
        </text>
      </g>

      <!-- Layer separator lines -->
      <g class="layer-lines">
        <line
          v-for="x in [60, 380, 720, 1060, 1160]"
          :key="'vline-'+x"
          :x1="x"
          y1="32"
          :x2="x"
          y2="800"
          stroke="rgba(255,255,255,0.04)"
          stroke-width="1"
        />
      </g>

      <!-- ==== Links ==== -->
      <g class="sankey-links">
        <path
          v-for="(link, i) in positionedLinks"
          :key="'link-'+i"
          :d="link.path"
          :stroke="link.color"
          :stroke-width="link.width"
          fill="none"
          :opacity="linkOpacity.has(i) ? 0.08 : (hoveredLink === i ? 0.85 : 0.35)"
          :style="{
            transition: 'opacity 0.2s ease, stroke-width 0.2s ease',
            cursor: 'pointer',
          }"
          @mouseenter="hoveredLink = i"
          @mouseleave="hoveredLink = null"
          @mousemove="(e: MouseEvent) => showTooltip(e,
            `${link.source.label} → ${link.target.label}: ${link.value.toLocaleString()} 次出手`)"
          @mouseout="hideTooltip"
        />
      </g>

      <!-- ==== Nodes ==== -->
      <g class="sankey-nodes">
        <g
          v-for="node in positionedNodes"
          :key="node.id"
          :class="['sankey-node', { selected: isSelected(node) }]"
          :style="{ cursor: 'pointer' }"
          @click="onNodeClick(node)"
          @mouseenter="showTooltip($event, nodeTooltip(node))"
          @mouseleave="hideTooltip"
        >
          <!-- Node rectangle -->
          <rect
            :x="node.x"
            :y="node.y"
            :width="colWidth(node.layer)"
            :height="Math.max(node.height, 1)"
            rx="4"
            ry="4"
            :fill="getNodeFill(node)"
            :stroke="hoveredNode === node.id ? NODE_STROKE_HOVER : getNodeBorderColor(node)"
            :stroke-width="isSelected(node) ? 3 : 1.5"
            :opacity="
              (props.selectedTimeBin != null && props.selectedTimeBin >= 0 && node.layer !== 1)
                ? 0.4 : 1
            "
            :style="{
              transition: 'opacity 0.2s ease, stroke-width 0.2s ease',
            }"
            @mouseenter="hoveredNode = node.id"
            @mouseleave="hoveredNode = null"
          />

          <!-- Node label -->
          <text
            :x="node.x + colWidth(node.layer) / 2"
            :y="node.y + node.height / 2 - 4"
            text-anchor="middle"
            :fill="node.layer === 4 ? '#fff' : '#e6edf3'"
            font-size="11"
            font-weight="500"
          >
            {{ node.label }}
          </text>

          <!-- Node size label -->
          <text
            v-if="node.height > 24"
            :x="node.x + colWidth(node.layer) / 2"
            :y="node.y + node.height / 2 + 12"
            text-anchor="middle"
            fill="#8b949e"
            font-size="9"
          >
            {{ fmtCount(node.size) }}
          </text>

          <!-- L2 FG% indicator -->
          <text
            v-if="node.layer === 2 && node.meta?.fg_pct !== undefined && node.height > 36"
            :x="node.x + colWidth(node.layer) / 2"
            :y="node.y + node.height / 2 + 26"
            text-anchor="middle"
            :fill="node.meta.fg_pct >= 0.50 ? '#00B42A' : '#8b949e'"
            font-size="10"
            font-weight="600"
          >
            {{ (node.meta.fg_pct * 100).toFixed(1) }}%
          </text>
        </g>
      </g>

      <!-- ==== Tooltip ==== -->
      <g v-if="tooltip.visible" class="tooltip" style="pointer-events: none">
        <rect
          :x="tooltip.x - 8"
          :y="tooltip.y - 20"
          :width="tooltip.text.length * 7 + 16"
          height="24"
          rx="4"
          fill="rgba(13,17,23,0.92)"
          stroke="rgba(255,255,255,0.15)"
          stroke-width="1"
        />
        <text
          :x="tooltip.x"
          :y="tooltip.y - 4"
          fill="#e6edf3"
          font-size="12"
        >
          {{ tooltip.text }}
        </text>
      </g>
    </svg>
  </div>
</template>

<script lang="ts">
/** Column width for a given layer */
function colWidth(layer: number): number {
  const w = [100, 120, 120, 90] as const
  return w[layer - 1] ?? 100
}

/** Format count for display */
function fmtCount(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

/** Generate tooltip text for a node */
function nodeTooltip(node: SankeyNode): string {
  const count = node.size.toLocaleString()
  if (node.layer === 2 && node.meta?.fg_pct !== undefined) {
    const fg = (node.meta.fg_pct * 100).toFixed(1)
    return `${node.label}: ${count} 出手, FG% ${fg}%`
  }
  if (node.layer === 4) {
    return `${node.label}: ${count} 次`
  }
  return `${node.label}: ${count} 出手`
}
</script>

<style scoped>
.sankey-chart {
  position: relative;
  width: 100%;
}

/* SVG container */
.sankey-svg {
  width: 100%;
  height: auto;
  display: block;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
}

/* === Loading / Empty states === */
.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 480px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(255, 255, 255, 0.12);
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.state-text {
  font-size: 14px;
  color: #8b949e;
  margin: 0;
}

.state-icon { font-size: 32px; }

.state-detail {
  font-size: 12px;
  color: #5c6670;
  margin: 0;
}

/* === Node interactions === */
.sankey-node {
  transition: opacity 0.15s ease;
}

.sankey-node.selected rect {
  filter: brightness(1.3);
}
</style>
