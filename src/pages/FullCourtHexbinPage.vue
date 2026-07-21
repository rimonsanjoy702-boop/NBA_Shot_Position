<script setup lang="ts">
/**
 * FullCourtHexbinPage.vue — Full-court hexbin heatmap with accurate dimensions.
 *
 * Scale: 1 ft = 10 px. Full court 94 ft × 50 ft = 940 px × 500 px.
 * viewBox: "0 0 1100 600"
 *
 * User selects two half-court data views independently.
 * Same hexbin JSON data as Classic view — only the coordinate transform differs.
 */
import { ref, computed, watch } from 'vue';
import type { HalfCourtSelection, HexbinCell } from '@/models';
import { ALL_SEASONS } from '@/models';
import { fetchHexbinSeason, extractHexbins, getAvailableTeams, getAvailablePlayers } from '@/hexbin-data';
import FullCourtBaseLayer from '@/components/FullCourtBaseLayer.vue';
import FullCourtHexbinLayer from '@/components/FullCourtHexbinLayer.vue';

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

function scopeLabel(scope: string) {
  const m: Record<string, string> = { league: '联盟', team: '球队', player: '球员' };
  return m[scope] ?? '';
}

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

// ═══════════════════════════════════════════════════════════
// Computed props for layers
// ═══════════════════════════════════════════════════════════
const layerLoading = computed(() => pageState.value === 'loading');
const layerError = computed(() => pageState.value === 'error' ? errorDetail.value : '');
</script>

<template>
  <div class="full-court-page">
    <!-- ── Header ── -->
    <header class="page-header">
      <h1 class="page-title">🏀 全场 Hexbin 热力图</h1>
      <p class="page-subtitle">正确尺寸全场视图 · 独立左右半场对比 · 23 赛季</p>
    </header>

    <!-- ── Controls ── -->
    <div class="controls-bar">
      <!-- Left side controls -->
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
        <span v-if="leftSelection.entityLabel" class="info-label">{{ leftSelection.entityLabel }}</span>
        <span class="cell-count">{{ leftCells.length.toLocaleString() }} 格</span>
      </div>

      <!-- Center spacer -->
      <div class="center-ctrl">
        <span class="vs-label">VS</span>
      </div>

      <!-- Right side controls -->
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
        <span v-if="rightSelection.entityLabel" class="info-label">{{ rightSelection.entityLabel }}</span>
        <span class="cell-count">{{ rightCells.length.toLocaleString() }} 格</span>
      </div>

      <el-button v-if="pageState === 'error'" type="primary" size="small" @click="refreshAll">重试</el-button>
    </div>

    <!-- ── Court ── -->
    <div class="court-wrapper">
      <FullCourtBaseLayer />
      <FullCourtHexbinLayer :cells="leftCells" side="left" :loading="layerLoading" :error="layerError" />
      <FullCourtHexbinLayer :cells="rightCells" side="right" :loading="layerLoading" :error="layerError" />

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
      <div class="color-strip">
        <span class="color-dot" style="background:#fbe3c8" /><span class="color-dot" style="background:#f4a460" />
        <span class="color-dot" style="background:#e8733a" /><span class="color-dot" style="background:#c9381a" />
        <span class="color-dot" style="background:#9e1206" /><span class="color-dot" style="background:#7a0b02" />
      </div>
      <span class="legend-end">0%</span>
      <span class="legend-end">100%</span>
      <span class="legend-divider">|</span>
      <span class="legend-label">出手量</span>
      <svg width="20" height="20" viewBox="0 0 20 20">
        <polygon :points="(()=>{const p=[];for(let i=0;i<6;i++){const a=Math.PI/180*60*i;p.push(`${(10+4*Math.cos(a)).toFixed(1)},${(10+4*Math.sin(a)).toFixed(1)}`)}return p.join(' ')})()" fill="var(--text-secondary, #8b949e)" opacity="0.5" />
      </svg>
      <svg width="28" height="28" viewBox="0 0 28 28">
        <polygon :points="(()=>{const p=[];for(let i=0;i<6;i++){const a=Math.PI/180*60*i;p.push(`${(14+10*Math.cos(a)).toFixed(1)},${(14+10*Math.sin(a)).toFixed(1)}`)}return p.join(' ')})()" fill="var(--text-secondary, #8b949e)" opacity="0.5" />
      </svg>
      <span class="legend-note">少 → 多</span>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════ Page layout ═══════════════════════ */
.full-court-page {
  min-height: 100vh;
  background: var(--bg-root, #0d1117);
  padding: var(--space-lg, 24px) var(--space-xl, 32px) var(--space-xl, 32px);
  display: flex;
  flex-direction: column;
  gap: var(--space-md, 16px);
  max-width: 1200px;
  margin: 0 auto;
}

/* ═══════════════════════ Header ═══════════════════════ */
.page-header { text-align: center; }
.page-title { font-size: var(--fs-hero, 32px); font-weight: 800; color: var(--text-primary, #e6edf3); margin: 0; }
.page-subtitle { font-size: var(--fs-subtitle, 14px); color: var(--text-secondary, #8b949e); margin: var(--space-xs, 4px) 0 0; }

/* ═══════════════════════ Controls ═══════════════════════ */
.controls-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--space-sm, 8px);
  padding: var(--space-sm, 8px) var(--space-md, 16px);
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-md, 8px);
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
  padding: 0 var(--space-sm, 8px);
}
.vs-label {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-tertiary, #5c6670);
  letter-spacing: 2px;
}
.info-label {
  font-size: var(--fs-caption, 11px);
  color: var(--accent-primary, #3498db);
  font-weight: 600;
  white-space: nowrap;
}
.cell-count {
  font-size: var(--fs-caption, 11px);
  color: var(--text-tertiary, #5c6670);
  white-space: nowrap;
}

/* ═══════════════════════ Court ═══════════════════════ */
.court-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 1100 / 600;
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-lg, 10px);
  overflow: hidden;
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
  padding: var(--space-sm, 8px) var(--space-md, 16px);
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-md, 8px);
}
.legend-label { font-size: var(--fs-caption, 11px); color: var(--text-secondary, #8b949e); margin-right: 4px; }
.color-strip { display: flex; gap: 1px; }
.color-dot { width: 22px; height: 12px; border-radius: 2px; }
.legend-end { font-size: 10px; color: var(--text-tertiary, #5c6670); }
.legend-divider { color: var(--border-card, rgba(255,255,255,0.08)); margin: 0 8px; }
.legend-note { font-size: 10px; color: var(--text-tertiary, #5c6670); }
</style>
