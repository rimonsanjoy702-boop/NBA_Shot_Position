<script setup lang="ts">
/**
 * HexbinLayer.vue — Renders half-court hexbin data as an SVG <g> overlay.
 *
 * Props:
 *   cells:      HexbinCell[] from JSON data
 *   side:       'left' | 'right' — which half-court
 *   colorRange: [minFG, maxFG] — for color scale (optional; defaults to data range)
 *
 * Coordinate transform (JSON original → viewBox):
 *   Left:  viewX = 150 + y,  viewY = 250 + x
 *   Right: viewX = 1730 - y, viewY = 250 + x
 */
import { computed } from 'vue';
import type { HexbinCell } from '../types';
import { fgPctColor } from '../fgPctColor';

const props = withDefaults(defineProps<{
  cells: HexbinCell[];
  side: 'left' | 'right';
}>(), {
  cells: () => [],
});

// ---- Derived data ranges ----
const countExtent = computed(() => {
  if (!props.cells.length) return [1, 100] as const;
  const counts = props.cells.map((c) => c.count);
  return [Math.min(...counts), Math.max(...counts)] as const;
});

// ---- Coordinate transform ----
function toViewCoords(x: number, y: number): { vx: number; vy: number } {
  if (props.side === 'left') {
    return { vx: 150 + y, vy: 500 + x };
  }
  return { vx: 1730 - y, vy: 500 + x };
}

// ---- Size mapping: count → hex radius ----
const RADIUS_MIN = 3;
const RADIUS_MAX = 22;

function countToRadius(count: number): number {
  const [cMin, cMax] = countExtent.value;
  if (cMax === cMin) return (RADIUS_MIN + RADIUS_MAX) / 2;
  // sqrt scale — area proportional to count
  const t = (Math.sqrt(count) - Math.sqrt(cMin)) / (Math.sqrt(cMax) - Math.sqrt(cMin));
  return RADIUS_MIN + t * (RADIUS_MAX - RADIUS_MIN);
}

// ---- Hexagon path (pointy-top, given center and radius) ----
function hexPath(cx: number, cy: number, r: number): string {
  const points: string[] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i - 30); // pointy-top
    const px = cx + r * Math.cos(angle);
    const py = cy + r * Math.sin(angle);
    points.push(`${px.toFixed(1)},${py.toFixed(1)}`);
  }
  return points.join(' ');
}

// ---- Tooltip ----
function formatTooltip(cell: HexbinCell): string {
  return [
    `投篮次数: ${cell.count.toLocaleString()}`,
    `命中率: ${(cell.fg_pct * 100).toFixed(1)}%`,
  ].join('\n');
}

// ---- Build hex items for v-for ----
const hexItems = computed(() =>
  props.cells.map((cell) => {
    const { vx, vy } = toViewCoords(cell.x, cell.y);
    const r = countToRadius(cell.count);
    const color = fgPctColor(cell.fg_pct);
    return { cell, vx, vy, r, color, path: hexPath(vx, vy, r) };
  })
);
</script>

<template>
  <g :id="`hexbin-${side}`" class="hexbin-layer">
    <g
      v-for="(item, i) in hexItems"
      :key="`${item.cell.x}-${item.cell.y}-${i}`"
      class="hex-cell"
    >
      <title>{{ formatTooltip(item.cell) }}</title>
      <polygon
        :points="item.path"
        :fill="item.color"
        :stroke="item.color"
        stroke-width="0.5"
        opacity="0.85"
      />
    </g>
  </g>
</template>

<style scoped>
.hex-cell polygon {
  transition: opacity 150ms ease-out;
}
.hex-cell:hover polygon {
  opacity: 1;
  stroke: rgba(255, 255, 255, 0.6);
  stroke-width: 1;
}
</style>
