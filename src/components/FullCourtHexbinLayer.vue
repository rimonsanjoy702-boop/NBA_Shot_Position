<script setup lang="ts">
/**
 * FullCourtHexbinLayer.vue — Hexbin overlay for accurate full-court SVG.
 *
 * Transform: 90° rotation of classic "basket-at-bottom" coordinates.
 * Same JSON data, zero changes to preprocessing.
 *
 * Left basket (132.5, 300):  viewX = 132.5 + dataY,  viewY = 300 + dataX
 * Right basket (967.5, 300): viewX = 967.5 - dataY,  viewY = 300 + dataX
 *
 * Clip-path ensures hexbins don't bleed past midcourt.
 */
import { computed } from 'vue';
import type { HexbinCell } from '@/models';
import { fgPctColorClassic } from '@/util/fgPctColorClassic';

const props = withDefaults(defineProps<{
  cells: HexbinCell[];
  side: 'left' | 'right';
  loading?: boolean;
  error?: string;
}>(), {
  cells: () => [],
  loading: false,
  error: '',
});

// ── Geometry ──
const L_BASKET_X = 132.5;
const R_BASKET_X = 967.5;
const BASKET_Y = 300;
const MIDCOURT_X = 550;

const COURT_L = 80;
const COURT_R = 1020;
const COURT_T = 50;
const COURT_B = 550;

// ── Coord transform: rotate 90° from classic "basket bottom" orientation ──
function toViewX(dataX: number, dataY: number): number {
  if (props.side === 'left') {
    // Basket at left baseline → shoot right
    return L_BASKET_X + dataY;
  }
  // Basket at right baseline → shoot left (mirror)
  return R_BASKET_X - dataY;
}

function toViewY(dataX: number): number {
  return BASKET_Y + dataX;
}

// ── Hex size mapping ──
const SIZE_MIN = 2;
const SIZE_MAX = 18;

const countExtent = computed(() => {
  if (!props.cells.length) return { min: 1, max: 100 };
  const counts = props.cells.map((c) => c.count);
  return { min: Math.min(...counts), max: Math.max(...counts) };
});

function countToRadius(count: number): number {
  const { min, max } = countExtent.value;
  if (max === min) return (SIZE_MIN + SIZE_MAX) / 2;
  const t = (Math.sqrt(count) - Math.sqrt(min)) / (Math.sqrt(max) - Math.sqrt(min));
  return SIZE_MIN + t * (SIZE_MAX - SIZE_MIN);
}

// ── Flat-top hexagon path ──
function fp(cx: number, cy: number, r: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 180) * (60 * i);
    pts.push(`${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`);
  }
  return pts.join(' ');
}

function tip(cell: HexbinCell): string {
  return `X: ${cell.x}  Y: ${cell.y}\n出手: ${cell.count.toLocaleString()}\n命中率: ${(cell.fg_pct * 100).toFixed(1)}%`;
}

const hexItems = computed(() => {
  return props.cells
    .map((cell) => {
      const vx = toViewX(cell.x, cell.y);
      const vy = toViewY(cell.x);
      const r = countToRadius(cell.count);
      const color = fgPctColorClassic(cell.fg_pct);
      return { key: `${props.side}-${cell.x}-${cell.y}`, p: fp(vx, vy, r), color, r, tip: tip(cell) };
    })
    .sort((a, b) => b.r - a.r);
});
</script>

<template>
  <svg
    class="fchl-overlay"
    viewBox="0 0 1100 600"
    preserveAspectRatio="xMidYMid meet"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <!-- Clip to half-court: left [COURT_L, MIDCOURT_X], right (MIDCOURT_X, COURT_R] -->
      <clipPath v-if="side === 'left'" :id="`fc-clip-${side}`">
        <rect :x="COURT_L" :y="COURT_T" :width="MIDCOURT_X - COURT_L" :height="COURT_B - COURT_T" />
      </clipPath>
      <clipPath v-else :id="`fc-clip-${side}`">
        <rect :x="MIDCOURT_X" :y="COURT_T" :width="COURT_R - MIDCOURT_X" :height="COURT_B - COURT_T" />
      </clipPath>
    </defs>

    <g v-if="cells.length > 0 && !loading" :clip-path="`url(#fc-clip-${side})`">
      <g v-for="h in hexItems" :key="h.key" class="fc-hc">
        <title>{{ h.tip }}</title>
        <polygon :points="h.p" :fill="h.color" opacity="0.8" />
      </g>
    </g>

    <!-- Basket marker on top of hexbins -->
    <circle
      v-if="side === 'left'"
      :cx="L_BASKET_X" :cy="BASKET_Y" r="7"
      fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5"
    />
    <circle
      v-else
      :cx="R_BASKET_X" :cy="BASKET_Y" r="7"
      fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5"
    />
  </svg>
</template>

<style scoped>
.fchl-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.fc-hc polygon {
  transition: opacity .12s ease-out;
  pointer-events: auto;
}
.fc-hc:hover polygon {
  opacity: 1;
  stroke: rgba(255,255,255,0.5);
  stroke-width: 1;
}
</style>
