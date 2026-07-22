<script setup lang="ts">
/**
 * HexbinClassicPage.vue — Classic "basket-at-bottom" hexbin heatmap page.
 *
 * Single half-court view. User selects:
 *   - Scope:  league / team / player
 *   - Season: any of 23 seasons
 *   - Entity: specific team or player (when applicable)
 *
 * Data flows: user action → local state → HexbinClassicLayer re-renders.
 *
 * Three states: loading, empty, error — rendered inside the layer component.
 */
import { ref, computed, watch } from 'vue';
import type { HalfCourtSelection, HexbinCell } from '@/models';
import { ALL_SEASONS } from '@/models';
import { fetchHexbinSeason, extractHexbins, getAvailableTeams, getAvailablePlayers } from '@/hexbin-data';
import HexbinClassicLayer from '@/components/HexbinClassicLayer.vue';

// ===== State =====
type PageState = 'loading' | 'ready' | 'error';

const pageState = ref<PageState>('loading');
const errorMessage = ref('');
const errorDetail = ref('');

const selection = ref<HalfCourtSelection>({
  scope: 'league',
  season: '2018-19',
});
const cells = ref<HexbinCell[]>([]);
const teams = ref<{ id: number; name: string; abbr: string }[]>([]);
const players = ref<{ id: number; name: string }[]>([]);

const seasonCache = ref<Map<string, any>>(new Map());

// ===== Computed =====
const scopeLabel = computed(() => {
  const map: Record<string, string> = { league: '联盟', team: '球队', player: '球员' };
  return map[selection.value.scope] ?? '';
});

const entityChoices = computed(() => {
  if (selection.value.scope === 'team') return teams.value;
  if (selection.value.scope === 'player') return players.value;
  return [];
});

// ===== Data loading =====
async function loadData() {
  pageState.value = 'loading';
  errorMessage.value = '';
  errorDetail.value = '';

  try {
    let seasonData: any;
    if (seasonCache.value.has(selection.value.season)) {
      seasonData = seasonCache.value.get(selection.value.season);
    } else {
      seasonData = await fetchHexbinSeason(selection.value.season);
      seasonCache.value.set(selection.value.season, seasonData);
    }

    teams.value = getAvailableTeams(seasonData);
    players.value = getAvailablePlayers(seasonData);

    cells.value = extractHexbins(
      seasonData,
      selection.value.scope,
      selection.value.entityId,
    );

    pageState.value = 'ready';
  } catch (e: any) {
    errorMessage.value = '数据加载失败';
    errorDetail.value = e.message || '请检查网络连接后重试';
    pageState.value = 'error';
  }
}

// ===== Handlers =====
function onScopeChange(scope: 'league' | 'team' | 'player') {
  selection.value = { ...selection.value, scope, entityId: undefined };
}
function onEntityChange(id: number) {
  const entity = entityChoices.value.find((e) => e.id === id);
  selection.value = { ...selection.value, entityId: id, entityLabel: entity?.name };
}
function onSeasonChange(season: string) {
  selection.value = { ...selection.value, season };
}

// ===== Watchers =====
watch(selection, () => loadData(), { deep: true });

// ===== Init =====
loadData();

// ===== Computed props for layer =====
const layerLoading = computed(() => pageState.value === 'loading');
const layerError = computed(() => pageState.value === 'error' ? errorDetail.value : '');
</script>

<template>
  <div class="classic-page">
    <!-- ===== Header ===== -->
    <header class="page-header">
      <h1 class="page-title">🏀 Hexbin 投篮热力图</h1>
      <p class="page-subtitle">经典篮筐在下视图 · 半场 · 单赛季</p>
    </header>

    <!-- ===== Controls ===== -->
    <div class="controls-bar">
      <!-- Scope selector -->
      <div class="control-group">
        <span class="ctrl-label">粒度</span>
        <el-select
          :model-value="selection.scope"
          @update:model-value="onScopeChange"
          size="small"
          style="width: 80px"
        >
          <el-option label="联盟" value="league" />
          <el-option label="球队" value="team" />
          <el-option label="球员" value="player" />
        </el-select>

        <!-- Entity selector (when scope is team or player) -->
        <el-select
          v-if="selection.scope !== 'league'"
          :model-value="selection.entityId ?? null"
          @update:model-value="onEntityChange"
          size="small"
          style="width: 150px"
          filterable
          placeholder="选择..."
        >
          <el-option
            v-for="e in entityChoices"
            :key="e.id"
            :label="e.name"
            :value="e.id"
          />
        </el-select>
      </div>

      <!-- Season selector -->
      <div class="control-group">
        <span class="ctrl-label">赛季</span>
        <el-select
          :model-value="selection.season"
          @update:model-value="onSeasonChange"
          size="small"
          style="width: 110px"
        >
          <el-option
            v-for="s in ALL_SEASONS"
            :key="s"
            :label="s"
            :value="s"
          />
        </el-select>
      </div>

      <!-- Info badge -->
      <div class="control-group">
        <span class="info-badge">
          {{ cells.length.toLocaleString() }} 个格子
        </span>
        <span v-if="selection.entityLabel" class="info-badge info-name">
          {{ selection.entityLabel }}
        </span>
      </div>

      <!-- Retry button on error -->
      <el-button
        v-if="pageState === 'error'"
        type="primary"
        size="small"
        @click="loadData"
      >
        重新加载
      </el-button>
    </div>

    <!-- ===== Court + Hexbin ===== -->
    <HexbinClassicLayer
      :cells="cells"
      :loading="layerLoading"
      :error="layerError"
    />

    <!-- ===== Legend ===== -->
    <div class="legend-bar">
      <span class="legend-label">FG%</span>
      <div class="color-strip">
        <span class="color-dot" style="background:#fbe3c8" />
        <span class="color-dot" style="background:#f4a460" />
        <span class="color-dot" style="background:#e8733a" />
        <span class="color-dot" style="background:#c9381a" />
        <span class="color-dot" style="background:#9e1206" />
        <span class="color-dot" style="background:#7a0b02" />
      </div>
      <span class="legend-end">0%</span>
      <span class="legend-end">100%</span>

      <span class="legend-divider">|</span>

      <span class="legend-label">出手量</span>
      <svg width="20" height="20" viewBox="0 0 20 20">
        <polygon
          :points="(() => {
            const cx=10,cy=10,r=4,pts=[];
            for(let i=0;i<6;i++) {
              const a=(Math.PI/180)*(60*i);
              pts.push(`${(cx+r*Math.cos(a)).toFixed(1)},${(cy+r*Math.sin(a)).toFixed(1)}`);
            }
            return pts.join(' ');
          })()"
          fill="var(--text-secondary, #8b949e)"
          opacity="0.5"
        />
      </svg>
      <svg width="28" height="28" viewBox="0 0 28 28">
        <polygon
          :points="(() => {
            const cx=14,cy=14,r=10,pts=[];
            for(let i=0;i<6;i++) {
              const a=(Math.PI/180)*(60*i);
              pts.push(`${(cx+r*Math.cos(a)).toFixed(1)},${(cy+r*Math.sin(a)).toFixed(1)}`);
            }
            return pts.join(' ');
          })()"
          fill="var(--text-secondary, #8b949e)"
          opacity="0.5"
        />
      </svg>
      <span class="legend-note">少 → 多</span>
    </div>
  </div>
</template>

<style scoped>
/* ===== Page layout ===== */
.classic-page {
  min-height: 100vh;
  background: var(--bg-root, #0d1117);
  padding: var(--space-lg, 24px) var(--space-xl, 32px) var(--space-xl, 32px);
  display: flex;
  flex-direction: column;
  gap: var(--space-md, 16px);
  max-width: 800px;
  margin: 0 auto;
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

/* ===== Controls ===== */
.controls-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--space-md, 16px);
  padding: var(--space-sm, 8px) var(--space-md, 16px);
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-md, 8px);
}

.control-group {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 8px);
}

.ctrl-label {
  font-size: var(--fs-caption, 11px);
  font-weight: 600;
  color: var(--text-secondary, #8b949e);
  white-space: nowrap;
}

.info-badge {
  font-size: var(--fs-caption, 11px);
  color: var(--text-tertiary, #5c6670);
  white-space: nowrap;
}
.info-name {
  color: var(--accent-primary, #3498db);
  font-weight: 600;
}

/* ===== Legend ===== */
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

.legend-label {
  font-size: var(--fs-caption, 11px);
  color: var(--text-secondary, #8b949e);
  margin-right: 4px;
}

.color-strip {
  display: flex;
  gap: 1px;
}

.color-dot {
  width: 20px;
  height: 12px;
  border-radius: 2px;
}

.legend-end {
  font-size: 10px;
  color: var(--text-tertiary, #5c6670);
}

.legend-divider {
  color: var(--border-card, rgba(255,255,255,0.08));
  margin: 0 8px;
}

.legend-note {
  font-size: 10px;
  color: var(--text-tertiary, #5c6670);
}
</style>
