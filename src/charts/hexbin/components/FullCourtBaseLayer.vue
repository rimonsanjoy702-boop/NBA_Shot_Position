<script setup lang="ts">
/**
 * FullCourtBaseLayer.vue — Accurate NBA full-court SVG floor.
 *
 * Scale: 1 ft = 10 px
 * Full court: 94 ft × 50 ft = 940 px × 500 px
 * viewBox: "0 0 1100 600" (margins: left 80, right 80, top 50, bottom 50)
 *
 * Verified against memory/nba-court-dimensions.md (1:1 mapping).
 */

const L  = (): string => 'var(--court-line, rgba(255,255,255,0.22))';
const L2 = (): string => 'var(--court-line, rgba(255,255,255,0.16))';

// ── Geometry constants ──
const COURT_L = 80;
const COURT_R = 1020;
const COURT_T = 50;
const COURT_B = 550;

const MIDCOURT_X = 550;
const CENTER_Y = 300;
const CENTER_R = 60;       // 6 ft

const L_BASKET_X = 132.5;  // 80 + 52.5 (5.25 ft baseline→basket)
const R_BASKET_X = 967.5;  // 1020 - 52.5
const BASKET_Y = 300;

const THREE_R = 237.5;     // 23.75 ft
const THREE_SIDE = 30;     // 3 ft inside sideline

// 3pt arc intersection with sideline straights
// arc: (x - basketX)² + (y - 300)² = 237.5², at y = 50+30=80 (top) or 550-30=520 (bottom)
// (x - basketX)² = 237.5² - 220² = 56406.25 - 48400 = 8006.25
// |x - basketX| = 89.48
const ARC_DX = Math.sqrt(237.5 * 237.5 - 220 * 220);

const L_ARC_X = L_BASKET_X + ARC_DX;   // ≈ 222
const R_ARC_X = R_BASKET_X - ARC_DX;   // ≈ 878

const THREE_TOP = COURT_T + THREE_SIDE;     // 80
const THREE_BOT = COURT_B - THREE_SIDE;     // 520

// Paint: 16 ft wide × 19 ft deep from baseline
const PAINT_W = 160;  // 16 ft
const PAINT_D = 190;  // 19 ft
const PAINT_T = BASKET_Y - PAINT_W / 2;  // 220
const PAINT_B = BASKET_Y + PAINT_W / 2;  // 380

const L_PAINT_R = COURT_L + PAINT_D;     // 270 (FT line)
const R_PAINT_L = COURT_R - PAINT_D;     // 830

const FT_R = 60;       // 6 ft FT half-circle
const RESTRICT_R = 40; // 4 ft restricted arc

// Hash mark positions: 4 marks starting 7 ft from baseline, spaced 3 ft
function hashXLeft(i: number): number { return COURT_L + 70 + (i - 1) * 30; }
function hashXRight(i: number): number { return COURT_R - 70 - (i - 1) * 30; }
</script>

<template>
  <svg
    viewBox="0 0 1100 600"
    preserveAspectRatio="xMidYMid meet"
    class="fcs"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- ── Floor background ── -->
    <rect x="0" y="0" width="1100" height="600" fill="var(--bg-court-floor, #8c6239)" />

    <!-- ── Court outline (sidelines + baselines) ── -->
    <rect
      :x="COURT_L" :y="COURT_T"
      :width="COURT_R - COURT_L" :height="COURT_B - COURT_T"
      fill="none" :stroke="L()" stroke-width="2"
    />

    <!-- ── Center line ── -->
    <line :x1="MIDCOURT_X" :y1="COURT_T" :x2="MIDCOURT_X" :y2="COURT_B" :stroke="L()" stroke-width="2" />

    <!-- ── Center circle ── -->
    <circle :cx="MIDCOURT_X" :cy="CENTER_Y" :r="CENTER_R" fill="none" :stroke="L2()" stroke-width="1.5" />
    <circle :cx="MIDCOURT_X" :cy="CENTER_Y" r="3" fill="var(--court-line, rgba(255,255,255,0.3))" />

    <!-- ═══════════════════════ LEFT HALF ═══════════════════════ -->

    <!-- 3pt arc (curves toward midcourt / right) -->
    <path
      :d="`M ${L_ARC_X},${THREE_TOP} A ${THREE_R},${THREE_R} 0 0,1 ${L_ARC_X},${THREE_BOT}`"
      fill="none" :stroke="L()" stroke-width="1.5"
    />
    <!-- 3pt side straights (parallel to sidelines) -->
    <line :x1="COURT_L" :y1="THREE_TOP" :x2="L_ARC_X" :y2="THREE_TOP" :stroke="L()" stroke-width="1.5" />
    <line :x1="COURT_L" :y1="THREE_BOT" :x2="L_ARC_X" :y2="THREE_BOT" :stroke="L()" stroke-width="1.5" />

    <!-- Paint / Key -->
    <rect
      :x="COURT_L" :y="PAINT_T"
      :width="PAINT_D" :height="PAINT_W"
      fill="none" :stroke="L2()" stroke-width="1"
    />

    <!-- FT half-circle (above FT line, toward midcourt) -->
    <path
      :d="`M ${L_PAINT_R},${BASKET_Y - FT_R} A ${FT_R},${FT_R} 0 0,1 ${L_PAINT_R},${BASKET_Y + FT_R}`"
      fill="none" :stroke="L2()" stroke-width="1"
    />

    <!-- Restricted area arc (toward baseline / left) -->
    <path
      :d="`M ${L_BASKET_X},${BASKET_Y - RESTRICT_R} A ${RESTRICT_R},${RESTRICT_R} 0 0,1 ${L_BASKET_X},${BASKET_Y + RESTRICT_R}`"
      fill="none" :stroke="L2()" stroke-width="1"
    />

    <!-- Lane hash marks — top side (extend downward into paint) -->
    <line v-for="i in 4" :key="'lth'+i"
      :x1="hashXLeft(i)" :y1="PAINT_T"
      :x2="hashXLeft(i)" :y2="PAINT_T + 20"
      :stroke="L2()" stroke-width="1"
    />
    <!-- Lane hash marks — bottom side (extend upward into paint) -->
    <line v-for="i in 4" :key="'lbh'+i"
      :x1="hashXLeft(i)" :y1="PAINT_B"
      :x2="hashXLeft(i)" :y2="PAINT_B - 20"
      :stroke="L2()" stroke-width="1"
    />

    <!-- Left basket -->
    <circle :cx="L_BASKET_X" :cy="BASKET_Y" r="8" fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5" />
    <circle :cx="L_BASKET_X" :cy="BASKET_Y" r="2.5" fill="var(--semantic-rim, #e74c3c)" />

    <!-- ═══════════════════════ RIGHT HALF ═══════════════════════ -->

    <!-- 3pt arc (curves toward midcourt / left) -->
    <path
      :d="`M ${R_ARC_X},${THREE_TOP} A ${THREE_R},${THREE_R} 0 0,0 ${R_ARC_X},${THREE_BOT}`"
      fill="none" :stroke="L()" stroke-width="1.5"
    />
    <!-- 3pt side straights -->
    <line :x1="COURT_R" :y1="THREE_TOP" :x2="R_ARC_X" :y2="THREE_TOP" :stroke="L()" stroke-width="1.5" />
    <line :x1="COURT_R" :y1="THREE_BOT" :x2="R_ARC_X" :y2="THREE_BOT" :stroke="L()" stroke-width="1.5" />

    <!-- Paint / Key -->
    <rect
      :x="R_PAINT_L" :y="PAINT_T"
      :width="PAINT_D" :height="PAINT_W"
      fill="none" :stroke="L2()" stroke-width="1"
    />

    <!-- FT half-circle -->
    <path
      :d="`M ${R_PAINT_L},${BASKET_Y - FT_R} A ${FT_R},${FT_R} 0 0,0 ${R_PAINT_L},${BASKET_Y + FT_R}`"
      fill="none" :stroke="L2()" stroke-width="1"
    />

    <!-- Restricted area arc (toward baseline / right) -->
    <path
      :d="`M ${R_BASKET_X},${BASKET_Y - RESTRICT_R} A ${RESTRICT_R},${RESTRICT_R} 0 0,0 ${R_BASKET_X},${BASKET_Y + RESTRICT_R}`"
      fill="none" :stroke="L2()" stroke-width="1"
    />

    <!-- Lane hash marks — top side -->
    <line v-for="i in 4" :key="'rth'+i"
      :x1="hashXRight(i)" :y1="PAINT_T"
      :x2="hashXRight(i)" :y2="PAINT_T + 20"
      :stroke="L2()" stroke-width="1"
    />
    <!-- Lane hash marks — bottom side -->
    <line v-for="i in 4" :key="'rbh'+i"
      :x1="hashXRight(i)" :y1="PAINT_B"
      :x2="hashXRight(i)" :y2="PAINT_B - 20"
      :stroke="L2()" stroke-width="1"
    />

    <!-- Right basket -->
    <circle :cx="R_BASKET_X" :cy="BASKET_Y" r="8" fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5" />
    <circle :cx="R_BASKET_X" :cy="BASKET_Y" r="2.5" fill="var(--semantic-rim, #e74c3c)" />
  </svg>
</template>

<style scoped>
.fcs {
  display: block;
  width: 100%;
  height: auto;
}
</style>
