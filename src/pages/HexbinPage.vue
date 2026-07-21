<script setup lang="ts">
/**
 * HexbinPage.vue — Main page for the Hexbin Shot Position Heatmap.
 *
 * Architecture: Two-layer SVG overlay
 *   Layer 0: CourtBaseLayer (static court floor + lines — never re-renders)
 *   Layer 1: HexbinLayer × 2 (left + right half-court data overlays)
 *
 * State: local only (independent component per §3d of dev workflow).
 *        Pinia Store integration comes later in Step 4.
 */
import { ref, computed, watch } from 'vue';
import type { HalfCourtSelection, HexbinCell } from '@/models';
import { fetchHexbinSeason, extractHexbins, getAvailableTeams, getAvailablePlayers } from '@/hexbin-data';
import CourtBaseLayer from '@/components/CourtBaseLayer.vue';
import HexbinLayer from '@/components/HexbinLayer.vue';
import HexbinControls from '@/components/HexbinControls.vue';
import HexbinLegend from '@/components/HexbinLegend.vue';

// ---- State ----
type LoadingState = 'loading' | 'ready' | 'empty' | 'error';

const loadingState = ref<LoadingState>('loading');
const errorMessage = ref('');

// Half-court selections
const leftSelection = ref<HalfCourtSelection>({
  scope: 'league',
  season: '2018-19',
});
const rightSelection = ref<HalfCourtSelection>({
  scope: 'league',
  season: '2018-19',
});

// Loaded season data cache
const seasonCache = ref<Map<string, any>>(new Map());

// Available entities for the selected seasons
const leftTeams = ref<{ id: number; name: string; abbr: string }[]>([]);
const leftPlayers = ref<{ id: number; name: string }[]>([]);
const rightTeams = ref<{ id: number; name: string; abbr: string }[]>([]);
const rightPlayers = ref<{ id: number; name: string }[]>([]);

// Current hexbin cells
const leftCells = ref<HexbinCell[]>([]);
const rightCells = ref<HexbinCell[]>([]);

// ---- Data loading ----
async function loadSeason(season: string): Promise<any> {
  if (seasonCache.value.has(season)) {
    return seasonCache.value.get(season);
  }
  const data = await fetchHexbinSeason(season);
  seasonCache.value.set(season, data);
  return data;
}

async function refreshLeft() {
  try {
    const data = await loadSeason(leftSelection.value.season);
    leftTeams.value = getAvailableTeams(data);
    leftPlayers.value = getAvailablePlayers(data);
    leftCells.value = extractHexbins(
      data,
      leftSelection.value.scope,
      leftSelection.value.entityId,
    );
  } catch (e: any) {
    throw e;
  }
}

async function refreshRight() {
  try {
    const data = await loadSeason(rightSelection.value.season);
    rightTeams.value = getAvailableTeams(data);
    rightPlayers.value = getAvailablePlayers(data);
    rightCells.value = extractHexbins(
      data,
      rightSelection.value.scope,
      rightSelection.value.entityId,
    );
  } catch (e: any) {
    throw e;
  }
}

async function refreshAll() {
  loadingState.value = 'loading';
  errorMessage.value = '';
  try {
    await Promise.all([refreshLeft(), refreshRight()]);
    loadingState.value = 'ready';
  } catch (e: any) {
    errorMessage.value = e.message || '数据加载失败';
    loadingState.value = 'error';
  }
}

// ---- Watchers ----
watch(leftSelection, () => { refreshLeft(); }, { deep: true });
watch(rightSelection, () => { refreshRight(); }, { deep: true });

// ---- Init ----
refreshAll();
</script>

<template>
  <div class="hexbin-page">
    <!-- Page title -->
    <header class="page-header">
      <h1 class="page-title">🏀 投篮分布 Hexbin 热力图</h1>
      <p class="page-subtitle">全场对比 · 三级粒度 · 23 赛季</p>
    </header>

    <!-- Controls -->
    <HexbinControls
      :teams="leftTeams"
      :players="leftPlayers"
      :left-selection="leftSelection"
      :right-selection="rightSelection"
      @update:left-selection="leftSelection = $event"
      @update:right-selection="rightSelection = $event"
    />

    <!-- === Loading state === -->
    <div v-if="loadingState === 'loading'" class="state-box">
      <div class="spinner" />
      <p class="state-text">加载数据中...</p>
    </div>

    <!-- === Error state === -->
    <div v-else-if="loadingState === 'error'" class="state-box">
      <span class="state-icon">⚠️</span>
      <p class="state-text error-text">数据加载失败</p>
      <p class="state-detail">{{ errorMessage }}</p>
      <el-button type="primary" size="small" @click="refreshAll">重新加载</el-button>
    </div>

    <!-- === Main court + hexbin layers === -->
    <div v-else class="court-container">
      <!-- Layer 0: Court base (static) -->
      <CourtBaseLayer />

      <!-- Layer 1: Hexbin overlays (absolute positioned over court) -->
      <svg
        class="hexbin-overlay"
        viewBox="0 0 1880 1000"
        preserveAspectRatio="xMidYMid meet"
        xmlns="http://www.w3.org/2000/svg"
      >
        <HexbinLayer :cells="leftCells" side="left" />
        <HexbinLayer :cells="rightCells" side="right" />
      </svg>

      <!-- Empty overlay when no data -->
      <div v-if="leftCells.length === 0 && rightCells.length === 0" class="empty-overlay">
        <span class="empty-icon">🏀</span>
        <p class="empty-text">暂无投篮数据</p>
        <p class="empty-detail">该筛选条件下没有投篮记录</p>
      </div>
    </div>

    <!-- Legend -->
    <HexbinLegend />
  </div>
</template>

<style scoped>
/* ===== Page layout ===== */
.hexbin-page {
  min-height: 100vh;
  background: var(--bg-root, #0d1117);
  padding: var(--space-lg, 24px) var(--space-xl, 32px) var(--space-xl, 32px);
  display: flex;
  flex-direction: column;
  gap: var(--space-md, 16px);
}

/* ===== Header ===== */
.page-header {
  text-align: center;
}
.page-title {
  font-size: var(--fs-hero, 32px);
  font-weight: 800;
  color: var(--text-primary, #e6edf3);
  margin: 0;
}
.page-subtitle {
  font-size: var(--fs-subtitle, 14px);
  color: var(--text-secondary, #8b949e);
  margin: var(--space-xs, 4px) 0 0;
}

/* ===== Court container ===== */
.court-container {
  position: relative;
  width: 100%;
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-lg, 10px);
  overflow: hidden;
  background: var(--bg-card, rgba(255,255,255,0.04));
}

/* Hexbin layer: exactly overlaps the court base */
.hexbin-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* allow hover on polygons through to the SVG */
}
.hexbin-overlay :deep(.hex-cell) {
  pointer-events: auto; /* hex cells are interactive */
}

/* ===== States — three-state pattern (视觉规范 §6) ===== */
.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm, 8px);
  min-height: 320px;
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-lg, 10px);
}

/* Loading spinner (视觉规范 §6.1) */
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: var(--accent-primary, #3498db);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.state-text {
  font-size: var(--fs-body, 14px);
  color: var(--text-secondary, #8b949e);
  margin: 0;
}
.error-text {
  color: var(--semantic-missed, #ff6b6b);
}
.state-detail {
  font-size: var(--fs-caption, 12px);
  color: var(--text-tertiary, #5c6670);
  margin: 0;
}
.state-icon {
  font-size: 32px;
}

/* Empty overlay (视觉规范 §6.2) */
.empty-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs, 4px);
  pointer-events: none;
}
.empty-icon {
  font-size: 40px;
}
.empty-text {
  font-size: var(--fs-body, 14px);
  color: var(--text-secondary, #8b949e);
  margin: 0;
}
.empty-detail {
  font-size: var(--fs-caption, 12px);
  color: var(--text-tertiary, #5c6670);
  margin: 0;
}
</style>
