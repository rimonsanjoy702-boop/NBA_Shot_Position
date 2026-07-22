<script setup lang="ts">
/**
 * SankeyDemoPage.vue — Demo page for the sankey chart.
 *
 * Left / right half-court each have independent season / scope / entity selectors.
 * Clicking the left/right tab switches which side is displayed as a single chart.
 */

import { ref, computed, watch, shallowRef } from 'vue'
import { fetchSankeySeason, extractSankeyData, getAvailableTeams, getAvailablePlayers } from './sankey-data'
import type { SankeySeasonData, SankeyNode, SankeyLink, LoadingState, Scope, EntityOption, CourtSide } from './types'
import { ALL_SEASONS } from './types'
import SankeyChart from './SankeyChart.vue'
import type { SankeySelection } from './types'

// ============================================================================
// State — left & right each have independent selection state
// ============================================================================

const activeSide = ref<CourtSide>('left')

const leftSelection = ref<SankeySelection>({ scope: 'league', season: '2014-15' })
const rightSelection = ref<SankeySelection>({ scope: 'league', season: '2014-15' })

// Each side has its own loaded data cache
const leftData = ref<SankeySeasonData | null>(null)
const rightData = ref<SankeySeasonData | null>(null)

// Each side has its own entity lists
const leftTeams = shallowRef<EntityOption[]>([])
const leftPlayers = shallowRef<EntityOption[]>([])
const rightTeams = shallowRef<EntityOption[]>([])
const rightPlayers = shallowRef<EntityOption[]>([])

const loadingState = ref<LoadingState>('loading')
const errorMessage = ref('')

const nodes = ref<SankeyNode[]>([])
const links = ref<SankeyLink[]>([])

// Interaction state by layer
const selectedTimeBin = ref<number>(-1)
const selectedZone = ref<string | null>(null)
const selectedAction = ref<string | null>(null)
const selectedOutcome = ref<string | null>(null)

// ============================================================================
// Derived — current active selection
// ============================================================================

const currentSelection = computed(() =>
  activeSide.value === 'left' ? leftSelection.value : rightSelection.value
)

const currentData = computed(() =>
  activeSide.value === 'left' ? leftData.value : rightData.value
)

const currentTeams = computed(() =>
  activeSide.value === 'left' ? leftTeams.value : rightTeams.value
)

const currentPlayers = computed(() =>
  activeSide.value === 'left' ? leftPlayers.value : rightPlayers.value
)

const entityOptions = computed(() =>
  currentSelection.value.scope === 'team' ? currentTeams.value : currentPlayers.value
)

const title = computed(() => {
  const sideLabel = activeSide.value === 'left' ? '左半场' : '右半场'
  const sel = currentSelection.value
  let scopeLabel = '联盟'
  if (sel.scope === 'team') {
    const team = currentTeams.value.find(t => t.id === sel.entityId)
    scopeLabel = team ? team.name : '球队'
  } else if (sel.scope === 'player') {
    const player = currentPlayers.value.find(p => p.id === sel.entityId)
    scopeLabel = player ? player.name : '球员'
  }
  return `投篮结构 · ${sel.season} · ${sideLabel} · ${scopeLabel}`
})

// ============================================================================
// Data loading — load one side (season may differ between sides)
// ============================================================================

const seasonCache = ref<Map<string, SankeySeasonData>>(new Map())

async function loadSeason(season: string): Promise<SankeySeasonData> {
  if (seasonCache.value.has(season)) return seasonCache.value.get(season)!
  const data = await fetchSankeySeason(season)
  seasonCache.value.set(season, data)
  return data
}

async function loadSide(side: CourtSide) {
  const sel = side === 'left' ? leftSelection.value : rightSelection.value
  const data = await loadSeason(sel.season)
  if (side === 'left') {
    leftData.value = data
    leftTeams.value = getAvailableTeams(data)
    leftPlayers.value = getAvailablePlayers(data)
  } else {
    rightData.value = data
    rightTeams.value = getAvailableTeams(data)
    rightPlayers.value = getAvailablePlayers(data)
  }
}

function refreshActiveChart() {
  const data = currentData.value
  if (!data) return
  const sel = currentSelection.value
  const result = extractSankeyData(data, sel.scope, sel.entityId)
  nodes.value = result.nodes
  links.value = result.links
  loadingState.value = result.nodes.length > 0 ? 'ready' : 'empty'
  selectedTimeBin.value = -1
  selectedZone.value = null
  selectedAction.value = null
  selectedOutcome.value = null
}

// ============================================================================
// Watchers — re-fetch when season changes, re-extract when scope/entity/side changes
// ============================================================================

async function onLeftSelectionChange() {
  await loadSide('left')
  if (activeSide.value === 'left') refreshActiveChart()
}

async function onRightSelectionChange() {
  await loadSide('right')
  if (activeSide.value === 'right') refreshActiveChart()
}

watch(() => leftSelection.value.season, onLeftSelectionChange)
watch(() => rightSelection.value.season, onRightSelectionChange)
watch(() => leftSelection.value.scope, () => { if (activeSide.value === 'left') refreshActiveChart() })
watch(() => rightSelection.value.scope, () => { if (activeSide.value === 'right') refreshActiveChart() })
watch(() => leftSelection.value.entityId, () => { if (activeSide.value === 'left') refreshActiveChart() })
watch(() => rightSelection.value.entityId, () => { if (activeSide.value === 'right') refreshActiveChart() })

// Switching side → just re-extract from the other side's cached data
watch(activeSide, () => {
  refreshActiveChart()
})

// ============================================================================
// Selection setter helpers (bound by v-model style in template)
// ============================================================================

function setSelection(side: CourtSide, patch: Partial<SankeySelection>) {
  if (side === 'left') {
    leftSelection.value = { ...leftSelection.value, ...patch }
  } else {
    rightSelection.value = { ...rightSelection.value, ...patch }
  }
}

// ============================================================================
// Event handlers (chart clicks)
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
  selectedTimeBin.value = -1; selectedZone.value = null
  selectedAction.value = null; selectedOutcome.value = null
}

// ============================================================================
// Init — load both sides
// ============================================================================

async function init() {
  loadingState.value = 'loading'
  try {
    await Promise.all([loadSide('left'), loadSide('right')])
    refreshActiveChart()
  } catch (e: any) {
    errorMessage.value = e.message || '加载失败'
    loadingState.value = 'error'
  }
}
init()
</script>

<template>
  <div class="sankey-demo">
    <header class="demo-header">
      <h1 class="demo-title">🏀 {{ title }}</h1>
      <p class="demo-subtitle">四层桑基投篮结构图 · SVG 手绘</p>
    </header>

    <!-- Half-court tabs -->
    <div class="court-tabs">
      <button
        :class="['court-tab', { active: activeSide === 'left' }]"
        @click="activeSide = 'left'"
      >左半场</button>
      <button
        :class="['court-tab', { active: activeSide === 'right' }]"
        @click="activeSide = 'right'"
      >右半场</button>
    </div>

    <!-- Selection controls — for the active side -->
    <div class="controls-row">
      <div class="control-group">
        <span class="control-label">粒度</span>
        <select
          :value="currentSelection.scope"
          @change="setSelection(activeSide, { scope: ($event.target as HTMLSelectElement).value as Scope, entityId: undefined })"
          class="scope-select"
        >
          <option value="league">联盟</option>
          <option value="team">球队</option>
          <option value="player">球员</option>
        </select>
      </div>

      <div v-if="currentSelection.scope !== 'league'" class="control-group">
        <span class="control-label">{{ currentSelection.scope === 'team' ? '球队' : '球员' }}</span>
        <select
          :value="currentSelection.entityId"
          @change="setSelection(activeSide, { entityId: Number(($event.target as HTMLSelectElement).value) || undefined })"
          class="entity-select"
        >
          <option :value="undefined">-- 请选择 --</option>
          <option v-for="e in entityOptions" :key="e.id" :value="e.id">{{ e.name }}</option>
        </select>
      </div>

      <div class="control-group">
        <span class="control-label">赛季</span>
        <select
          :value="currentSelection.season"
          @change="setSelection(activeSide, { season: ($event.target as HTMLSelectElement).value })"
          class="season-select"
        >
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

    <div v-if="loadingState === 'error'" class="error-box">
      <span>⚠️ {{ errorMessage }}</span>
      <button class="retry-btn" @click="init">重试</button>
    </div>
  </div>
</template>

<style scoped>
.sankey-demo {
  min-height: 100vh;
  background: #0d1117;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.demo-header { text-align: center; }
.demo-title { font-size: 28px; font-weight: 800; color: #e6edf3; margin: 0; }
.demo-subtitle { font-size: 13px; color: #8b949e; margin: 4px 0 0; }

/* ---- Half-court tabs ---- */
.court-tabs {
  display: flex;
  gap: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.12);
  align-self: center;
}
.court-tab {
  padding: 8px 32px;
  font-size: 14px;
  font-weight: 600;
  color: #8b949e;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.court-tab:first-child { border-right: 1px solid rgba(255,255,255,0.08); }
.court-tab:hover { background: rgba(255,255,255,0.04); }
.court-tab.active { background: #3498db; color: #fff; }

/* ---- Controls ---- */
.controls-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 10px 16px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
.control-group { display: flex; align-items: center; gap: 8px; }
.control-label {
  font-size: 11px; font-weight: 600; color: #8b949e; text-transform: uppercase;
}
.scope-select, .entity-select, .season-select {
  padding: 4px 8px; font-size: 12px;
  background: rgba(255,255,255,0.06); color: #e6edf3;
  border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; cursor: pointer;
}
.entity-select { min-width: 160px; }
.scope-select option, .entity-select option, .season-select option {
  background: #1a1f2e; color: #e6edf3;
}

/* ---- Breadcrumb ---- */
.selection-breadcrumb {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: rgba(52,152,219,0.08);
  border: 1px solid rgba(52,152,219,0.2); border-radius: 6px;
  font-size: 12px; flex-wrap: wrap;
}
.breadcrumb-label { color: #8b949e; }
.breadcrumb-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 11px;
}
.time-chip { background: #d95926; }
.zone-chip { background: #199e70; }
.action-chip { background: #9085e9; }
.outcome-chip { background: #3987e5; }
.chip-close {
  border: none; background: transparent; color: inherit;
  font-size: 14px; cursor: pointer; padding: 0; line-height: 1;
}
.clear-all {
  font-size: 11px; color: #8b949e; background: transparent;
  border: none; cursor: pointer; text-decoration: underline;
}

/* ---- Error ---- */
.error-box {
  display: flex; align-items: center; justify-content: center; gap: 12px;
  padding: 24px; color: #ef4444;
  background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); border-radius: 8px;
}
.retry-btn {
  padding: 4px 12px; font-size: 12px; color: #e6edf3;
  background: #3498db; border: none; border-radius: 4px; cursor: pointer;
}
</style>
