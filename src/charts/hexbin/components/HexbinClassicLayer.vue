<script setup lang="ts">
/**
 * HexbinClassicLayer.vue — Classic basket-at-bottom half-court hexbin heatmap.
 *
 * viewBox: "0 0 600 600", scale: 1 ft = 10 viewBox units.
 *
 * NBA half-court (baseline → midcourt = 47 ft):
 *   - Basket:  5.25 ft from baseline → viewBox y=500
 *   - Baseline: y=552.5 (5.25 ft × 10 below basket)
 *   - Midcourt: y=82.5  (47 ft × 10 from baseline; 552.5-470=82.5)
 *   - Sidelines: x=50, x=550 (50 ft wide = 500 px)
 *
 * Data coordinates (from Python preprocessing):
 *   - 1 data unit = 0.1 ft (tenths of feet), basket at (0,0)
 *   - X: -250..250 maps 1:1 → viewX: 50..550 (50 ft via 10 px/ft)
 *   - Y: 0..470 maps 1:1 → viewY: 500..30 (0=basket, 470=47 ft out)
 *
 * Transform:
 *   viewX = 300 + dataX
 *   viewY = 500 - dataY
 */
import { computed } from 'vue';
import type { HexbinCell } from '../types';
import { fgPctColorClassic } from '../fgPctColorClassic';

const props = withDefaults(defineProps<{
  cells: HexbinCell[];
  loading?: boolean;
  error?: string;
}>(), {
  cells: () => [],
  loading: false,
  error: '',
});

// ═══════════════════════════════════════════════════════════
// NBA half-court geometry (basket-at-bottom, 10 px/ft)
// ═══════════════════════════════════════════════════════════

// --- Layout: world-space reference frame ---
// ft_from_baseline: 0 (baseline) → 47 (midcourt), 5.25 (basket)
// ft_from_center: -25 (left) → +25 (right)
// viewBox: 600×600, court = 500 px wide, 470 px tall

const VIEW_W = 600;
const VIEW_H = 600;

// Basket / center
const BASKET_X = 300;
const BASKET_Y = 500;                  // 5.25 ft below baseline = 52.5 px

// Court boundaries
const COURT_L = 50;                    // left sideline
const COURT_R = 550;                   // right sideline
const MIDCOURT_Y = 82.5;               // 47 ft from baseline → 470 px up
const BASELINE_Y = 552.5;              // 5.25 ft below basket → 52.5 px down

// 3pt arc: center (BASKET_X, BASKET_Y), radius 23.75 ft = 237.5 px
const THREE_R = 237.5;
// 3pt straight lines: 3 ft = 30 px inside each sideline
const THREE_SIDE = COURT_L + 30;       // 80
const THREE_SIDE_R = COURT_R - 30;     // 520

// Intersection of 3pt arc with side straights:
// arc equation: (x-300)² + (y-500)² = 237.5²
// at x = 80: 220² + (y-500)² = 237.5² → (y-500)² = 237.5² - 220² = 8012.5
// → y-500 = -89.52 → y = 410.48
const THREE_Y_ARC = BASKET_Y - Math.sqrt(237.5 * 237.5 - 220 * 220);

// Key/Paint: 16 ft wide × 19 ft deep from baseline
const PAINT_L = BASKET_X - 80;          // 16 ft = 160 px, 80 each side
const PAINT_R = BASKET_X + 80;
const PAINT_H = 190;                    // 19 ft = 190 px
const PAINT_T = BASELINE_Y - PAINT_H;   // 362.5
// FT line = paint top
const FT_LINE_Y = PAINT_T;

// FT half-circle: radius 6 ft = 60 px, centered on FT line midpoint
const FT_R = 60;

// Restricted area arc: radius 4 ft = 40 px from basket
const RESTRICT_R = 40;

// ── Coordinate transform from hex data to viewBox ──
// Data coordinates are in tenths of feet (10 units/ft), basket at (0,0).
// viewBox uses 10 px/ft — so 1 data unit = 1 viewBox px. 1:1 mapping.
function toViewX(dataX: number): number {
  return BASKET_X + dataX;
}
function toViewY(dataY: number): number {
  return BASKET_Y - dataY;
}

// ── Hex sizes ──
const SIZE_MIN = 1.5;
const SIZE_MAX = 15;

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
      const vx = toViewX(cell.x);
      const vy = toViewY(cell.y);
      const r = countToRadius(cell.count);
      const color = fgPctColorClassic(cell.fg_pct);
      return { key: `${cell.x}-${cell.y}`, p: fp(vx, vy, r), color, r, tip: tip(cell) };
    })
    .sort((a, b) => b.r - a.r);
});

// ── Stroke colors ──
const L = (): string => 'var(--court-line, rgba(255,255,255,0.22))';
const L2 = (): string => 'var(--court-line, rgba(255,255,255,0.16))';
</script>

<template>
  <div class="classic-court-wrapper">
    <!-- ── State overlays ── -->
    <div v-if="loading" class="ol"><div class="sp" /><p class="ot">加载数据中...</p></div>
    <div v-else-if="error" class="ol"><span class="oi">⚠️</span><p class="ot err">数据加载失败</p><p class="od">{{ error }}</p></div>
    <div v-else-if="cells.length === 0" class="ol"><span class="oi">🏀</span><p class="ot">暂无投篮数据</p><p class="od">该筛选条件下没有投篮记录</p></div>

    <svg viewBox="0 0 600 600" preserveAspectRatio="xMidYMid meet" class="s">
      <defs>
        <clipPath id="cclip">
          <rect :x="COURT_L" :y="MIDCOURT_Y" :width="COURT_R - COURT_L" :height="BASELINE_Y - MIDCOURT_Y" />
        </clipPath>
      </defs>

      <!-- Floor -->
      <rect x="0" y="0" :width="VIEW_W" :height="VIEW_H" fill="var(--bg-court-floor, #8c6239)" />

      <!-- ═══════════════════════ COURT LINES ═══════════════════════ -->

      <!-- Sidelines (left & right, from midcourt to baseline) -->
      <line :x1="COURT_L" :y1="MIDCOURT_Y" :x2="COURT_L" :y2="BASELINE_Y" :stroke="L()" stroke-width="2" />
      <line :x1="COURT_R" :y1="MIDCOURT_Y" :x2="COURT_R" :y2="BASELINE_Y" :stroke="L()" stroke-width="2" />

      <!-- Baselines -->
      <line :x1="COURT_L" :y1="BASELINE_Y" :x2="COURT_R" :y2="BASELINE_Y" :stroke="L()" stroke-width="2" />

      <!-- Midcourt line -->
      <line :x1="COURT_L" :y1="MIDCOURT_Y" :x2="COURT_R" :y2="MIDCOURT_Y" :stroke="L()" stroke-width="2" />

      <!-- 3pt arc (center at basket, sweeps ABOVE basket toward midcourt) -->
      <path
        :d="`M ${COURT_L + 30},${THREE_Y_ARC} A ${THREE_R},${THREE_R} 0 0,1 ${COURT_R - 30},${THREE_Y_ARC}`"
        fill="none" :stroke="L()" stroke-width="1.5"
      />
      <!-- 3pt straight lines down to baseline (3 ft inside sidelines) -->
      <line :x1="COURT_L + 30" :y1="THREE_Y_ARC" :x2="COURT_L + 30" :y2="BASELINE_Y" :stroke="L()" stroke-width="1.5" />
      <line :x1="COURT_R - 30" :y1="THREE_Y_ARC" :x2="COURT_R - 30" :y2="BASELINE_Y" :stroke="L()" stroke-width="1.5" />

      <!-- Key / Paint (16 ft wide × 19 ft deep from baseline) -->
      <rect
        :x="PAINT_L" :y="FT_LINE_Y"
        :width="PAINT_R - PAINT_L" :height="PAINT_H"
        fill="none" :stroke="L2()" stroke-width="1"
      />

      <!-- FT half-circle (above FT line, toward midcourt) -->
      <path
        :d="`M ${BASKET_X - FT_R},${FT_LINE_Y} A ${FT_R},${FT_R} 0 0,1 ${BASKET_X + FT_R},${FT_LINE_Y}`"
        fill="none" :stroke="L2()" stroke-width="1"
      />

      <!-- Restricted area arc (4 ft radius, below basket) -->
      <path
        :d="`M ${BASKET_X - RESTRICT_R},${BASKET_Y} A ${RESTRICT_R},${RESTRICT_R} 0 0,1 ${BASKET_X + RESTRICT_R},${BASKET_Y}`"
        fill="none" :stroke="L2()" stroke-width="1"
      />

      <!-- Lane hash marks (blocks on each side — 4 marks, 2 ft wide, starting 7 ft from baseline, 3 ft apart) -->
      <line v-for="m in 4" :key="'lm'+m"
        :x1="PAINT_L" :y1="BASELINE_Y - 70 - (m-1)*30"
        :x2="PAINT_L + 20" :y2="BASELINE_Y - 70 - (m-1)*30"
        :stroke="L2()" stroke-width="1"
      />
      <line v-for="m in 4" :key="'rm'+m"
        :x1="PAINT_R" :y1="BASELINE_Y - 70 - (m-1)*30"
        :x2="PAINT_R - 20" :y2="BASELINE_Y - 70 - (m-1)*30"
        :stroke="L2()" stroke-width="1"
      />

      <!-- Basket -->
      <circle :cx="BASKET_X" :cy="BASKET_Y" r="8" fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5" />
      <circle :cx="BASKET_X" :cy="BASKET_Y" r="2.5" fill="var(--semantic-rim, #e74c3c)" />

      <!-- ═══════════════════════ HEXBIN CELLS ═══════════════════════ -->
      <g v-if="cells.length > 0 && !loading" clip-path="url(#cclip)">
        <g v-for="h in hexItems" :key="h.key" class="hc">
          <title>{{ h.tip }}</title>
          <polygon :points="h.p" :fill="h.color" opacity="0.85" />
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.classic-court-wrapper {
  position: relative; width: 100%; aspect-ratio: 600 / 600;
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-lg, 10px); overflow: hidden;
}
.s { display: block; width: 100%; height: 100%; }
.hc polygon { transition: opacity .12s ease-out; }
.hc:hover polygon { opacity: 1; stroke: rgba(255,255,255,0.5); stroke-width: 1; }
.ol { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; z-index: 2; pointer-events: none; background: var(--bg-court-floor, #8c6239); }
.sp { width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.12); border-top-color: var(--accent-primary, #3498db); border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ot { font-size: 13px; color: var(--text-secondary, #8b949e); margin: 0; }
.err { color: var(--semantic-missed, #ff6b6b); }
.oi { font-size: 32px; }
.od { font-size: 11px; color: var(--text-tertiary, #5c6670); margin: 0; }
</style>
