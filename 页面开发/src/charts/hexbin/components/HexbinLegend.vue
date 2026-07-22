<script setup lang="ts">
/**
 * HexbinLegend.vue — Bottom color legend for hexbin heatmap.
 * Shows: FG% color bar (red → green) + size legend (small → large)
 */
import { fgPctColor } from '../fgPctColor';

const FG_STOPS = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0];
const SIZE_EXAMPLES = [
  { label: '少 (few)', r: 4 },
  { label: '多 (many)', r: 12 },
];
</script>

<template>
  <div class="hexbin-legend">
    <!-- FG% color bar -->
    <div class="legend-section">
      <span class="legend-label">命中率 FG%</span>
      <div class="color-bar">
        <div
          v-for="(stop, i) in FG_STOPS"
          :key="i"
          class="color-stop"
          :style="{ backgroundColor: fgPctColor(stop) }"
        >
          <span class="stop-label">{{ (stop * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <!-- Size legend -->
    <div class="legend-section">
      <span class="legend-label">投篮量</span>
      <div class="size-bar">
        <div
          v-for="(ex, i) in SIZE_EXAMPLES"
          :key="i"
          class="size-sample"
        >
          <svg :width="ex.r * 2 + 4" :height="ex.r * 2 + 4" viewBox="0 0 28 28">
            <polygon
              :points="hexagonPoints(ex.r + 2, ex.r + 2, ex.r)"
              fill="var(--text-secondary, #8b949e)"
              opacity="0.5"
            />
          </svg>
          <span>{{ ex.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
function hexagonPoints(cx: number, cy: number, r: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i - 30);
    pts.push(`${(cx + r * Math.cos(angle)).toFixed(1)},${(cy + r * Math.sin(angle)).toFixed(1)}`);
  }
  return pts.join(' ');
}
</script>

<style scoped>
.hexbin-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xl, 32px);
  padding: var(--space-sm, 8px) var(--space-md, 16px);
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-md, 8px);
}

.legend-section {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 8px);
}

.legend-label {
  font-size: var(--fs-caption, 11px);
  color: var(--text-secondary, #8b949e);
  white-space: nowrap;
}

.color-bar {
  display: flex;
  width: 240px;
  height: 14px;
  border-radius: 3px;
  overflow: hidden;
}

.color-stop {
  flex: 1;
  position: relative;
}

.stop-label {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: var(--text-tertiary, #5c6670);
  white-space: nowrap;
}

.size-bar {
  display: flex;
  align-items: center;
  gap: var(--space-md, 16px);
}

.size-sample {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 10px;
  color: var(--text-tertiary, #5c6670);
}
</style>
