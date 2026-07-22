<script setup lang="ts">
/**
 * HexbinPage.vue — Dashboard-embedded full-court hexbin heatmap.
 *
 * Accurate NBA full-court coordinate system:
 *   Scale: 1 ft = 10 px. Full court 94 ft × 50 ft.
 *   viewBox: "0 0 1100 600"
 *
 * Left basket at (132.5, 300), right basket at (967.5, 300).
 * All layers (floor + lines + hexbins) share ONE SVG for perfect alignment.
 */
import { ref, computed, watch } from 'vue';
import type { HalfCourtSelection, HexbinCell } from './types';
import { ALL_SEASONS } from './types';
import { fetchHexbinSeason, extractHexbins, getAvailableTeams, getAvailablePlayers } from './hexbin-data';
import { fgPctColorClassic } from './fgPctColorClassic';

// ═══════════════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════════════

type PageState = 'loading' | 'ready' | 'error';

const pageState = ref<PageState>('loading');
const errorMessage = ref('');
const errorDetail = ref('');

const leftSelection = ref<HalfCourtSelection>({ scope: 'league', season: '2018-19' });
const rightSelection = ref<HalfCourtSelection>({ scope: 'league', season: '2018-19' });
const leftCells = ref<HexbinCell[]>([]);
const rightCells = ref<HexbinCell[]>([]);
const leftTeams = ref<{ id: number; name: string; abbr: string }[]>([]);
const rightTeams = ref<{ id: number; name: string; abbr: string }[]>([]);
const leftPlayers = ref<{ id: number; name: string }[]>([]);
const rightPlayers = ref<{ id: number; name: string }[]>([]);
const seasonCache = ref<Map<string, any>>(new Map());

// ═══════════════════════════════════════════════════════════
// Data loading
// ═══════════════════════════════════════════════════════════

async function loadSeason(season: string): Promise<any> {
  if (seasonCache.value.has(season)) return seasonCache.value.get(season);
  const data = await fetchHexbinSeason(season);
  seasonCache.value.set(season, data);
  return data;
}

async function refreshSide(side: 'left' | 'right') {
  const sel = side === 'left' ? leftSelection.value : rightSelection.value;
  const data = await loadSeason(sel.season);
  if (side === 'left') {
    leftTeams.value = getAvailableTeams(data);
    leftPlayers.value = getAvailablePlayers(data);
    leftCells.value = extractHexbins(data, sel.scope, sel.entityId);
  } else {
    rightTeams.value = getAvailableTeams(data);
    rightPlayers.value = getAvailablePlayers(data);
    rightCells.value = extractHexbins(data, sel.scope, sel.entityId);
  }
}

async function refreshAll() {
  pageState.value = 'loading';
  errorMessage.value = '';
  errorDetail.value = '';
  try {
    await Promise.all([refreshSide('left'), refreshSide('right')]);
    pageState.value = 'ready';
  } catch (e: any) {
    errorMessage.value = '数据加载失败';
    errorDetail.value = e.message || '请检查网络连接后重试';
    pageState.value = 'error';
  }
}

watch(leftSelection, () => refreshSide('left'), { deep: true });
watch(rightSelection, () => refreshSide('right'), { deep: true });

refreshAll();

// ═══════════════════════════════════════════════════════════
// Handlers
// ═══════════════════════════════════════════════════════════

function entityChoices(side: 'left' | 'right') {
  const sel = side === 'left' ? leftSelection.value : rightSelection.value;
  if (sel.scope === 'team') return side === 'left' ? leftTeams.value : rightTeams.value;
  if (sel.scope === 'player') return side === 'left' ? leftPlayers.value : rightPlayers.value;
  return [];
}

function onScopeChange(side: 'left' | 'right', scope: 'league' | 'team' | 'player') {
  const ref_ = side === 'left' ? leftSelection : rightSelection;
  ref_.value = { ...ref_.value, scope, entityId: undefined };
}

function onEntityChange(side: 'left' | 'right', id: number) {
  const ref_ = side === 'left' ? leftSelection : rightSelection;
  const entities = entityChoices(side);
  const entity = entities.find((e: any) => e.id === id);
  ref_.value = { ...ref_.value, entityId: id, entityLabel: entity?.name };
}

function onSeasonChange(side: 'left' | 'right', season: string) {
  const ref_ = side === 'left' ? leftSelection : rightSelection;
  ref_.value = { ...ref_.value, season };
}

const layerLoading = computed(() => pageState.value === 'loading');
const layerError = computed(() => pageState.value === 'error' ? errorDetail.value : '');

// ═══════════════════════════════════════════════════════════
// Court geometry constants (same as FullCourtBaseLayer)
// ═══════════════════════════════════════════════════════════
const COURT_L = 80;
const COURT_R = 1020;
const COURT_T = 50;
const COURT_B = 550;
const MIDCOURT_X = 550;
const CENTER_Y = 300;
const CENTER_R = 60;

const L_BASKET_X = 132.5;
const R_BASKET_X = 967.5;
const BASKET_Y = 300;

const THREE_R = 237.5;
const THREE_SIDE = 30;
const ARC_DX = Math.sqrt(237.5 * 237.5 - 220 * 220);

const L_ARC_X = L_BASKET_X + ARC_DX;
const R_ARC_X = R_BASKET_X - ARC_DX;
const THREE_TOP = COURT_T + THREE_SIDE;
const THREE_BOT = COURT_B - THREE_SIDE;

const PAINT_W = 160;
const PAINT_D = 190;
const PAINT_T = BASKET_Y - PAINT_W / 2;
const PAINT_B = BASKET_Y + PAINT_W / 2;
const L_PAINT_R = COURT_L + PAINT_D;
const R_PAINT_L = COURT_R - PAINT_D;
const FT_R = 60;
const RESTRICT_R = 40;

function hashXLeft(i: number): number { return COURT_L + 70 + (i - 1) * 30; }
function hashXRight(i: number): number { return COURT_R - 70 - (i - 1) * 30; }

// ═══════════════════════════════════════════════════════════
// Hexbin layer computed data
// ═══════════════════════════════════════════════════════════
const SIZE_MIN = 2;
const SIZE_MAX = 18;

function countExt(cells: HexbinCell[]) {
  if (!cells.length) return { min: 1, max: 100 };
  const counts = cells.map(c => c.count);
  return { min: Math.min(...counts), max: Math.max(...counts) };
}

function countToRadius(count: number, ext: { min: number; max: number }): number {
  if (ext.max === ext.min) return (SIZE_MIN + SIZE_MAX) / 2;
  const t = (Math.sqrt(count) - Math.sqrt(ext.min)) / (Math.sqrt(ext.max) - Math.sqrt(ext.min));
  return SIZE_MIN + t * (SIZE_MAX - SIZE_MIN);
}

interface HexItem {
  key: string;
  p: string;
  color: string;
  r: number;
  tip: string;
}

const leftHexItems = computed<HexItem[]>(() => buildHexItems(leftCells.value, 'left'));
const rightHexItems = computed<HexItem[]>(() => buildHexItems(rightCells.value, 'right'));

function buildHexItems(cells: HexbinCell[], side: 'left' | 'right'): HexItem[] {
  const ext = countExt(cells);
  return cells
    .map(cell => {
      const vx = side === 'left' ? L_BASKET_X + cell.y : R_BASKET_X - cell.y;
      const vy = BASKET_Y + cell.x;
      const r = countToRadius(cell.count, ext);
      const color = fgPctColorClassic(cell.fg_pct);
      const tip = `X: ${cell.x}  Y: ${cell.y}\n出手: ${cell.count.toLocaleString()}\n命中率: ${(cell.fg_pct * 100).toFixed(1)}%`;
      const pts: string[] = [];
      for (let i = 0; i < 6; i++) {
        const a = (Math.PI / 180) * (60 * i - 30);
        pts.push(`${(vx + r * Math.cos(a)).toFixed(2)},${(vy + r * Math.sin(a)).toFixed(2)}`);
      }
      return { key: `${side}-${cell.x}-${cell.y}`, p: pts.join(' '), color, r, tip };
    })
    .sort((a, b) => b.r - a.r);
}
</script>

<template>
  <div class="hexbin-page">
    <!-- ── Header ── -->
    <div class="chart-header">
      <h1 class="chart-title">🏀 Hexbin 热力图</h1>
      <p class="chart-subtitle">独立左右半场对比 · 23 赛季</p>
    </div>

    <!-- ── Controls ── -->
    <div class="controls-bar">
      <div class="side-controls">
        <span class="side-label">左半场</span>
        <el-select :model-value="leftSelection.scope" @update:model-value="(v:any) => onScopeChange('left', v)" size="small" style="width:72px">
          <el-option label="联盟" value="league" />
          <el-option label="球队" value="team" />
          <el-option label="球员" value="player" />
        </el-select>
        <el-select
          v-if="leftSelection.scope !== 'league'"
          :model-value="leftSelection.entityId ?? null"
          @update:model-value="(v:any) => onEntityChange('left', v)"
          size="small" style="width:130px" filterable placeholder="选择..."
        >
          <el-option v-for="e in entityChoices('left')" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-select :model-value="leftSelection.season" @update:model-value="(v:any) => onSeasonChange('left', v)" size="small" style="width:100px">
          <el-option v-for="s in ALL_SEASONS" :key="s" :label="s" :value="s" />
        </el-select>
      </div>

      <div class="center-ctrl">
        <span class="vs-label">VS</span>
      </div>

      <div class="side-controls">
        <span class="side-label">右半场</span>
        <el-select :model-value="rightSelection.scope" @update:model-value="(v:any) => onScopeChange('right', v)" size="small" style="width:72px">
          <el-option label="联盟" value="league" />
          <el-option label="球队" value="team" />
          <el-option label="球员" value="player" />
        </el-select>
        <el-select
          v-if="rightSelection.scope !== 'league'"
          :model-value="rightSelection.entityId ?? null"
          @update:model-value="(v:any) => onEntityChange('right', v)"
          size="small" style="width:130px" filterable placeholder="选择..."
        >
          <el-option v-for="e in entityChoices('right')" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-select :model-value="rightSelection.season" @update:model-value="(v:any) => onSeasonChange('right', v)" size="small" style="width:100px">
          <el-option v-for="s in ALL_SEASONS" :key="s" :label="s" :value="s" />
        </el-select>
      </div>

      <el-button v-if="pageState === 'error'" type="primary" size="small" @click="refreshAll">重试</el-button>
    </div>

    <!-- ── Court SVG: floor + lines + hexbins all in ONE coordinate system ── -->
    <div class="court-wrapper">
      <svg
        viewBox="0 0 1100 600"
        preserveAspectRatio="xMidYMid meet"
        class="court-svg"
        xmlns="http://www.w3.org/2000/svg"
      >
        <!-- ═══════════════════ Floor background ═══════════════════ -->
        <rect x="0" y="0" width="1100" height="600" fill="var(--bg-court-floor, #8c6239)" />

        <!-- ═══════════════════ Court outline (sidelines + baselines) ═══════════════════ -->
        <rect
          :x="COURT_L" :y="COURT_T"
          :width="COURT_R - COURT_L" :height="COURT_B - COURT_T"
          fill="none" stroke="var(--court-line, rgba(255,255,255,0.22))" stroke-width="2"
        />

        <!-- ═══════════════════ Center line ═══════════════════ -->
        <line :x1="MIDCOURT_X" :y1="COURT_T" :x2="MIDCOURT_X" :y2="COURT_B" stroke="var(--court-line, rgba(255,255,255,0.22))" stroke-width="2" />

        <!-- ═══════════════════ Center circle ═══════════════════ -->
        <circle :cx="MIDCOURT_X" :cy="CENTER_Y" :r="CENTER_R" fill="none" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1.5" />
        <circle :cx="MIDCOURT_X" :cy="CENTER_Y" r="3" fill="var(--court-line, rgba(255,255,255,0.3))" />

        <!-- ═══════════════════ LEFT HALF ═══════════════════ -->
        <!-- 3pt arc -->
        <path :d="`M ${L_ARC_X},${THREE_TOP} A ${THREE_R},${THREE_R} 0 0,1 ${L_ARC_X},${THREE_BOT}`" fill="none" stroke="var(--court-line, rgba(255,255,255,0.22))" stroke-width="1.5" />
        <line :x1="COURT_L" :y1="THREE_TOP" :x2="L_ARC_X" :y2="THREE_TOP" stroke="var(--court-line, rgba(255,255,255,0.22))" stroke-width="1.5" />
        <line :x1="COURT_L" :y1="THREE_BOT" :x2="L_ARC_X" :y2="THREE_BOT" stroke="var(--court-line, rgba(255,255,255,0.22))" stroke-width="1.5" />

        <!-- Paint / Key -->
        <rect :x="COURT_L" :y="PAINT_T" :width="PAINT_D" :height="PAINT_W" fill="none" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />
        <path :d="`M ${L_PAINT_R},${BASKET_Y - FT_R} A ${FT_R},${FT_R} 0 0,1 ${L_PAINT_R},${BASKET_Y + FT_R}`" fill="none" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />
        <path :d="`M ${L_BASKET_X},${BASKET_Y - RESTRICT_R} A ${RESTRICT_R},${RESTRICT_R} 0 0,1 ${L_BASKET_X},${BASKET_Y + RESTRICT_R}`" fill="none" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />

        <!-- Lane hash marks -->
        <line v-for="i in 4" :key="'lth'+i" :x1="hashXLeft(i)" :y1="PAINT_T" :x2="hashXLeft(i)" :y2="PAINT_T + 20" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />
        <line v-for="i in 4" :key="'lbh'+i" :x1="hashXLeft(i)" :y1="PAINT_B" :x2="hashXLeft(i)" :y2="PAINT_B - 20" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />

        <!-- Left basket -->
        <circle :cx="L_BASKET_X" :cy="BASKET_Y" r="8" fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5" />
        <circle :cx="L_BASKET_X" :cy="BASKET_Y" r="2.5" fill="var(--semantic-rim, #e74c3c)" />

        <!-- ═══════════════════ RIGHT HALF ═══════════════════ -->
        <path :d="`M ${R_ARC_X},${THREE_TOP} A ${THREE_R},${THREE_R} 0 0,0 ${R_ARC_X},${THREE_BOT}`" fill="none" stroke="var(--court-line, rgba(255,255,255,0.22))" stroke-width="1.5" />
        <line :x1="COURT_R" :y1="THREE_TOP" :x2="R_ARC_X" :y2="THREE_TOP" stroke="var(--court-line, rgba(255,255,255,0.22))" stroke-width="1.5" />
        <line :x1="COURT_R" :y1="THREE_BOT" :x2="R_ARC_X" :y2="THREE_BOT" stroke="var(--court-line, rgba(255,255,255,0.22))" stroke-width="1.5" />

        <rect :x="R_PAINT_L" :y="PAINT_T" :width="PAINT_D" :height="PAINT_W" fill="none" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />
        <path :d="`M ${R_PAINT_L},${BASKET_Y - FT_R} A ${FT_R},${FT_R} 0 0,0 ${R_PAINT_L},${BASKET_Y + FT_R}`" fill="none" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />
        <path :d="`M ${R_BASKET_X},${BASKET_Y - RESTRICT_R} A ${RESTRICT_R},${RESTRICT_R} 0 0,0 ${R_BASKET_X},${BASKET_Y + RESTRICT_R}`" fill="none" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />

        <line v-for="i in 4" :key="'rth'+i" :x1="hashXRight(i)" :y1="PAINT_T" :x2="hashXRight(i)" :y2="PAINT_T + 20" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />
        <line v-for="i in 4" :key="'rbh'+i" :x1="hashXRight(i)" :y1="PAINT_B" :x2="hashXRight(i)" :y2="PAINT_B - 20" stroke="var(--court-line, rgba(255,255,255,0.16))" stroke-width="1" />

        <circle :cx="R_BASKET_X" :cy="BASKET_Y" r="8" fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5" />
        <circle :cx="R_BASKET_X" :cy="BASKET_Y" r="2.5" fill="var(--semantic-rim, #e74c3c)" />

        <!-- ═══════════════════ HEXBIN OVERLAYS ═══════════════════ -->
        <defs>
          <clipPath id="clip-left">
            <rect :x="COURT_L" :y="COURT_T" :width="MIDCOURT_X - COURT_L" :height="COURT_B - COURT_T" />
          </clipPath>
          <clipPath id="clip-right">
            <rect :x="MIDCOURT_X" :y="COURT_T" :width="COURT_R - MIDCOURT_X" :height="COURT_B - COURT_T" />
          </clipPath>
        </defs>

        <!-- Left hexbins -->
        <g v-if="leftCells.length > 0 && !layerLoading" clip-path="url(#clip-left)">
          <g v-for="h in leftHexItems" :key="h.key" class="hex-cell">
            <title>{{ h.tip }}</title>
            <polygon :points="h.p" :fill="h.color" opacity="0.8" />
          </g>
        </g>

        <!-- Right hexbins -->
        <g v-if="rightCells.length > 0 && !layerLoading" clip-path="url(#clip-right)">
          <g v-for="h in rightHexItems" :key="h.key" class="hex-cell">
            <title>{{ h.tip }}</title>
            <polygon :points="h.p" :fill="h.color" opacity="0.8" />
          </g>
        </g>
      </svg>

      <!-- State overlays -->
      <div v-if="layerLoading" class="ol"><div class="sp" /><p class="ot">加载数据中...</p></div>
      <div v-else-if="layerError" class="ol"><span class="oi">⚠️</span><p class="ot err">数据加载失败</p><p class="od">{{ errorDetail }}</p></div>
      <div v-else-if="leftCells.length === 0 && rightCells.length === 0" class="ol">
        <span class="oi">🏀</span><p class="ot">暂无投篮数据</p><p class="od">该筛选条件下没有投篮记录</p>
      </div>
    </div>

    <!-- ── Legend ── -->
    <div class="legend-bar">
      <span class="legend-label">命中率 FG%</span>
      <span class="legend-end">0%</span>
      <div class="color-strip">
        <span class="color-dot" style="background:#fbe3c8" /><span class="color-dot" style="background:#f4a460" />
        <span class="color-dot" style="background:#e8733a" /><span class="color-dot" style="background:#c9381a" />
        <span class="color-dot" style="background:#9e1206" /><span class="color-dot" style="background:#7a0b02" />
      </div>
      <span class="legend-end">100%</span>
      <span class="legend-divider">|</span>
      <span class="legend-label">出手量</span>
      <span class="legend-note">少</span>
      <svg width="20" height="20" viewBox="0 0 20 20">
        <polygon :points="(()=>{const p=[];for(let i=0;i<6;i++){const a=Math.PI/180*60*i;p.push(`${(10+4*Math.cos(a)).toFixed(1)},${(10+4*Math.sin(a)).toFixed(1)}`)}return p.join(' ')})()" fill="var(--text-secondary, #8b949e)" opacity="0.5" />
      </svg>
      <svg width="28" height="28" viewBox="0 0 28 28">
        <polygon :points="(()=>{const p=[];for(let i=0;i<6;i++){const a=Math.PI/180*60*i;p.push(`${(14+10*Math.cos(a)).toFixed(1)},${(14+10*Math.sin(a)).toFixed(1)}`)}return p.join(' ')})()" fill="var(--text-secondary, #8b949e)" opacity="0.5" />
      </svg>
      <span class="legend-note">多</span>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════ Page layout ═══════════════════════ */
.hexbin-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm, 8px);
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

/* ═══════════════════════ Header ═══════════════════════ */
.chart-header { text-align: center; flex-shrink: 0; }
.chart-title { font-size: var(--fs-hero, 32px); font-weight: 800; color: var(--text-primary, #e6edf3); margin: 0; }
.chart-subtitle { font-size: var(--fs-subtitle, 14px); color: var(--text-secondary, #8b949e); margin: var(--space-xs, 4px) 0 0; }

/* ═══════════════════════ Controls ═══════════════════════ */
.controls-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--space-sm, 8px);
  padding: 6px 12px;
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-md, 8px);
  flex-shrink: 0;
}
.side-controls {
  display: flex;
  align-items: center;
  gap: var(--space-xs, 6px);
}
.side-label {
  font-size: var(--fs-caption, 11px);
  font-weight: 700;
  color: var(--text-secondary, #8b949e);
  white-space: nowrap;
}
.center-ctrl {
  display: flex;
  align-items: center;
  padding: 0 4px;
}
.vs-label {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-tertiary, #5c6670);
  letter-spacing: 2px;
}

/* ═══════════════════════ Court ═══════════════════════ */
.court-wrapper {
  position: relative;
  width: 100%;
  flex: 1 1 auto;
  min-height: 0;
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-lg, 10px);
  overflow: hidden;
}

.court-svg {
  display: block;
  width: 100%;
  height: 100%;
}

/* ═══════════════════════ State overlays ═══════════════════════ */
.ol {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 4px; z-index: 4;
  pointer-events: none; background: var(--bg-court-floor, #8c6239);
}
.sp {
  width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.12);
  border-top-color: var(--accent-primary, #3498db); border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.ot { font-size: 13px; color: var(--text-secondary, #8b949e); margin: 0; }
.err { color: var(--semantic-missed, #ff6b6b); }
.oi { font-size: 32px; }
.od { font-size: 11px; color: var(--text-tertiary, #5c6670); margin: 0; }

/* ═══════════════════════ Legend ═══════════════════════ */
.legend-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs, 4px);
  padding: 6px 12px;
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-md, 8px);
  flex-shrink: 0;
}
.legend-label { font-size: var(--fs-caption, 11px); color: var(--text-secondary, #8b949e); margin-right: 4px; }
.color-strip { display: flex; gap: 1px; }
.color-dot { width: 22px; height: 12px; border-radius: 2px; }
.legend-end { font-size: 10px; color: var(--text-tertiary, #5c6670); }
.legend-divider { color: var(--border-card, rgba(255,255,255,0.08)); margin: 0 8px; }
.legend-note { font-size: 10px; color: var(--text-tertiary, #5c6670); }

.hex-cell polygon {
  transition: opacity .12s ease-out;
  pointer-events: auto;
}
.hex-cell:hover polygon {
  opacity: 1;
  stroke: rgba(255,255,255,0.5);
  stroke-width: 1;
}
</style>
