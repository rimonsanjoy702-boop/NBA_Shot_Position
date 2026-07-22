<script setup lang="ts">
/**
 * SankeyDemoPage.vue — Demo page for the sankey chart.
 *
 * Controls:
 *   - Court side: left / right (two-option toggle)
 *   - Season: dropdown (23 seasons)
 *   - Scope: dropdown (league / team / player)
 *   - Entity: dropdown (shown when scope is team or player)
 */

import { ref, computed, watch, shallowRef } from 'vue'
import { fetchSankeySeason, extractSankeyData, getAvailableTeams, getAvailablePlayers } from './sankey-data'
import type { SankeySeasonData, SankeyNode, SankeyLink, LoadingState, CourtSide, Scope, EntityOption } from './types'
import { ALL_SEASONS } from './types'
import SankeyChart from './SankeyChart.vue'

// ============================================================================
// State
// ============================================================================

const season = ref('2014-15')
const courtSide = ref<CourtSide>('left')
const scope = ref<Scope>('league')
const entityId = ref<number | undefined>(undefined)

const loadingState = ref<LoadingState>('loading')
const errorMessage = ref('')

const seasonData = ref<SankeySeasonData | null>(null)
const nodes = ref<SankeyNode[]>([])
const links = ref<SankeyLink[]>([])

// Entity list for the current season
const teams = shallowRef<EntityOption[]>([])
const players = shallowRef<EntityOption[]>([])

// Interaction state by layer
const selectedTimeBin = ref<number>(-1)
const selectedZone = ref<string | null>(null)
const selectedAction = ref<string | null>(null)
const selectedOutcome = ref<string | null>(null)

// ============================================================================
// Derived
// ============================================================================

const entityOptions = computed(() => scope.value === 'team' ? teams.value : players.value)

const title = computed(() => {
  const sideLabel = courtSide.value === 'left' ? '左半场' : '右半场'
  let scopeLabel = '联盟'
  if (scope.value === 'team') {
    const team = teams.value.find(t => t.id === entityId.value)
    scopeLabel = team ? team.name : '球队'
  } else if (scope.value === 'player') {
    const player = players.value.find(p => p.id === entityId.value)
    scopeLabel = player ? player.name : '球员'
  }
  return `投篮结构 · ${season.value} · ${sideLabel} · ${scopeLabel}`
})

// ============================================================================
// Data loading
// ============================================================================

async function loadData() {
  loadingState.value = 'loading'
  errorMessage.value = ''
  try {
    seasonData.value = await fetchSankeySeason(season.value)
    teams.value = getAvailableTeams(seasonData.value)
    players.value = getAvailablePlayers(seasonData.value)
    refreshExtraction()
  } catch (e: any) {
    errorMessage.value = e.message || '加载失败'
    loadingState.value = 'error'
  }
}

function refreshExtraction() {
  if (!seasonData.value) return
  const result = extractSankeyData(seasonData.value, scope.value, courtSide.value, entityId.value)
  nodes.value = result.nodes
  links.value = result.links
  loadingState.value = result.nodes.length > 0 ? 'ready' : 'empty'

  // Clear selections when switching
  selectedTimeBin.value = -1
  selectedZone.value = null
  selectedAction.value = null
  selectedOutcome.value = null
}

// ============================================================================
// Watchers
// ============================================================================

watch(season, () => { loadData() })
watch(courtSide, () => { refreshExtraction() })
watch(scope, () => {
  entityId.value = undefined
  refreshExtraction()
})
watch(entityId, () => { refreshExtraction() })

// ============================================================================
// Event handlers
// ============================================================================

function onSelectTimeBin(index: number) {
  selectedTimeBin.value = selectedTimeBin.value === index ? -1 : index
}

function onSelectZone(id: string) {
  selectedZone.value = selectedZone.value === id ? null : id
}

function onSelectAction(id: string) {
  selectedAction.value = selectedAction.value === id ? null : id
}

function onSelectOutcome(id: string) {
  selectedOutcome.value = selectedOutcome.value === id ? null : id
}

function clearAll() {
  selectedTimeBin.value = -1
  selectedZone.value = null
  selectedAction.value = null
  selectedOutcome.value = null
}

// ============================================================================
// Init
// ============================================================================

loadData()
</script>

<template>
  <div class="sankey-demo">
    <!-- Header -->
    <header class="demo-header">
      <h1 class="demo-title">🏀 {{ title }}</h1>
      <p class="demo-subtitle">四层桑基投篮结构图 · SVG 手绘</p>
    </header>

    <!-- Controls -->
    <div class="controls-row">
      <!-- Court side: left / right only -->
      <div class="control-group">
        <span class="control-label">半场</span>
        <div class="side-tabs">
          <button
            :class="['side-tab', { active: courtSide === 'left' }]"
            @click="courtSide = 'left'"
          >左半场</button>
          <button
            :class="['side-tab', { active: courtSide === 'right' }]"
            @click="courtSide = 'right'"
          >右半场</button>
        </div>
      </div>

      <!-- Scope: dropdown -->
      <div class="control-group">
        <span class="control-label">粒度</span>
        <select v-model="scope" class="scope-select">
          <option value="league">联盟</option>
          <option value="team">球队</option>
          <option value="player">球员</option>
        </select>
      </div>

      <!-- Entity: dropdown when scope is team/player -->
      <div v-if="scope !== 'league'" class="control-group">
        <span class="control-label">{{ scope === 'team' ? '球队' : '球员' }}</span>
        <select v-model="entityId" class="entity-select">
          <option :value="undefined">-- 请选择 --</option>
          <option
            v-for="e in entityOptions"
            :key="e.id"
            :value="e.id"
          >{{ e.name }}</option>
        </select>
      </div>

      <!-- Season -->
      <div class="control-group">
        <span class="control-label">赛季</span>
        <select v-model="season" class="season-select">
          <option v-for="s in ALL_SEASONS" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
    </div>

    <!-- Selection breadcrumb -->
    <div v-if="selectedTimeBin >= 0 || selectedZone || selectedAction || selectedOutcome" class="selection-breadcrumb">
      <span class="breadcrumb-label">已选：</span>
      <span v-if="selectedTimeBin >= 0" class="breadcrumb-chip time-chip">
        Q{{ Math.floor(selectedTimeBin / 2) + 1 }}{{ selectedTimeBin % 2 === 0 ? '前' : '后' }}
        <button class="chip-close" @click="selectedTimeBin = -1">×</button>
      </span>
      <span v-if="selectedZone" class="breadcrumb-chip zone-chip">
        {{ selectedZone }}
        <button class="chip-close" @click="selectedZone = null">×</button>
      </span>
      <span v-if="selectedAction" class="breadcrumb-chip action-chip">
        {{ selectedAction }}
        <button class="chip-close" @click="selectedAction = null">×</button>
      </span>
      <span v-if="selectedOutcome" class="breadcrumb-chip outcome-chip">
        {{ selectedOutcome }}
        <button class="chip-close" @click="selectedOutcome = null">×</button>
      </span>
      <button class="clear-all" @click="clearAll">清除全部</button>
    </div>

    <!-- Chart -->
    <SankeyChart
      :state="loadingState"
      :nodes="nodes"
      :links="links"
      :selected-time-bin="selectedTimeBin"
      :selected-zone="selectedZone"
      :selected-action="selectedAction"
      :selected-outcome="selectedOutcome"
      :title="title"
      @select-time-bin="onSelectTimeBin"
      @select-zone="onSelectZone"
      @select-action="onSelectAction"
      @select-outcome="onSelectOutcome"
    />

    <!-- Error state -->
    <div v-if="loadingState === 'error'" class="error-box">
      <span>⚠️ {{ errorMessage }}</span>
      <button class="retry-btn" @click="loadData">重试</button>
    </div>
  </div>
</template>

<style scoped>
/* ===== Layout ===== */
.sankey-demo {
  min-height: 100vh;
  background: #0d1117;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ===== Header ===== */
.demo-header { text-align: center; }
.demo-title {
  font-size: 28px;
  font-weight: 800;
  color: #e6edf3;
  margin: 0;
}
.demo-subtitle {
  font-size: 13px;
  color: #8b949e;
  margin: 4px 0 0;
}

/* ===== Controls ===== */
.controls-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 10px 16px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 11px;
  font-weight: 600;
  color: #8b949e;
  text-transform: uppercase;
}

/* Side tabs */
.side-tabs {
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.12);
}

.side-tab {
  padding: 4px 12px;
  font-size: 12px;
  color: #8b949e;
  background: transparent;
  border: none;
  border-right: 1px solid rgba(255,255,255,0.08);
  cursor: pointer;
  transition: background 0.15s;
}
.side-tab:last-child { border-right: none; }
.side-tab:hover { background: rgba(255,255,255,0.04); }
.side-tab.active {
  background: #3498db;
  color: #fff;
}

/* Dropdown selects */
.scope-select,
.entity-select,
.season-select {
  padding: 4px 8px;
  font-size: 12px;
  background: rgba(255,255,255,0.06);
  color: #e6edf3;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 6px;
  cursor: pointer;
  min-width: 80px;
}
.entity-select { min-width: 160px; }
.scope-select option,
.entity-select option,
.season-select option {
  background: #1a1f2e;
  color: #e6edf3;
}

/* ===== Breadcrumb ===== */
.selection-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(52,152,219,0.08);
  border: 1px solid rgba(52,152,219,0.2);
  border-radius: 6px;
  font-size: 12px;
  flex-wrap: wrap;
}

.breadcrumb-label { color: #8b949e; }

.breadcrumb-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  color: #fff;
  font-size: 11px;
}
.time-chip { background: #d95926; }
.zone-chip { background: #199e70; }
.action-chip { background: #9085e9; }
.outcome-chip { background: #3987e5; }

.chip-close {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
.clear-all {
  font-size: 11px;
  color: #8b949e;
  background: transparent;
  border: none;
  cursor: pointer;
  text-decoration: underline;
}

/* ===== Error ===== */
.error-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  color: #ef4444;
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: 8px;
}
.retry-btn {
  padding: 4px 12px;
  font-size: 12px;
  color: #e6edf3;
  background: #3498db;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
