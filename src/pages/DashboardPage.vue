<script setup lang="ts">
import { ref, computed, watch, onMounted, shallowRef } from 'vue'
import HexbinPage from '@/charts/hexbin/HexbinPage.vue'
import KdeChart from '@/charts/kde/KdeChart.vue'
import ThreePointCompareChart from '@/charts/three-point/components/ThreePointCompareChart.vue'
import TimeFgChart from '@/charts/time-fg/TimeFgChart.vue'
import SankeyChart from '@/charts/sankey/SankeyChart.vue'
import { useThreePointCompareStore, type AggDataMap } from '@/charts/three-point/store'
import { useTimeFilterStore } from '@/charts/time-fg/store'
import {
  fetchSankeySeason,
  extractSankeyData,
  getAvailableTeams,
  getAvailablePlayers,
} from '@/charts/sankey/sankey-data'
import type { SankeySeasonData, SankeyNode, SankeyLink, LoadingState, Scope, EntityOption, CourtSide, SankeySelection } from '@/charts/sankey/types'
import { ALL_SEASONS } from '@/charts/sankey/types'

// ── 三分数据 ──
const threeStore = useThreePointCompareStore()
const aggData = ref<AggDataMap>({})
const seasons3p = ref<string[]>([])

// ═══════════════════════════════════════════════════════════
// Sankey — Left / right half-court, independent selectors
// ═══════════════════════════════════════════════════════════

const sankeySide = ref<CourtSide>('left')

const leftSelection = ref<SankeySelection>({ scope: 'league', season: '2019-20' })
const rightSelection = ref<SankeySelection>({ scope: 'league', season: '2019-20' })

const leftData = ref<SankeySeasonData | null>(null)
const rightData = ref<SankeySeasonData | null>(null)

const leftTeams = shallowRef<EntityOption[]>([])
const leftPlayers = shallowRef<EntityOption[]>([])
const rightTeams = shallowRef<EntityOption[]>([])
const rightPlayers = shallowRef<EntityOption[]>([])

const sankeyState = ref<LoadingState>('loading')
const sankeyError = ref('')

const nodes = ref<SankeyNode[]>([])
const links = ref<SankeyLink[]>([])

// Selected chart nodes (breadcrumb, for hexbin linkage)
const selectedTimeBin = ref<number>(-1)
const selectedZone = ref<string | null>(null)
const selectedAction = ref<string | null>(null)
const selectedOutcome = ref<string | null>(null)

// ═══════ Derived — current active side ═══════

const currentSelection = computed(() =>
  sankeySide.value === 'left' ? leftSelection.value : rightSelection.value
)

const currentData = computed(() =>
  sankeySide.value === 'left' ? leftData.value : rightData.value
)

const currentTeams = computed(() =>
  sankeySide.value === 'left' ? leftTeams.value : rightTeams.value
)

const currentPlayers = computed(() =>
  sankeySide.value === 'left' ? leftPlayers.value : rightPlayers.value
)

const entityOptions = computed(() =>
  currentSelection.value.scope === 'team' ? currentTeams.value : currentPlayers.value
)

// ═══════ Data loading ═══════

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
  sankeyState.value = result.nodes.length > 0 ? 'ready' : 'empty'
  selectedTimeBin.value = -1
  selectedZone.value = null
  selectedAction.value = null
  selectedOutcome.value = null
}

// Season change → re-fetch, then re-extract
async function onLeftSeasonChange() {
  await loadSide('left')
  if (sankeySide.value === 'left') refreshActiveChart()
}
async function onRightSeasonChange() {
  await loadSide('right')
  if (sankeySide.value === 'right') refreshActiveChart()
}

watch(() => leftSelection.value.season, onLeftSeasonChange)
watch(() => rightSelection.value.season, onRightSeasonChange)

// Scope / entity change → re-extract from cached data
watch(() => leftSelection.value.scope, () => { if (sankeySide.value === 'left') refreshActiveChart() })
watch(() => rightSelection.value.scope, () => { if (sankeySide.value === 'right') refreshActiveChart() })
watch(() => leftSelection.value.entityId, () => { if (sankeySide.value === 'left') refreshActiveChart() })
watch(() => rightSelection.value.entityId, () => { if (sankeySide.value === 'right') refreshActiveChart() })

// Switch side → just re-extract from the other side's cached data
watch(sankeySide, () => refreshActiveChart())

// Helpers
function setSelection(side: CourtSide, patch: Partial<SankeySelection>) {
  if (side === 'left') {
    leftSelection.value = { ...leftSelection.value, ...patch }
  } else {
    rightSelection.value = { ...rightSelection.value, ...patch }
  }
}

// ── Chart event handlers ──
function onSelectTimeBin(idx: number) {
  selectedTimeBin.value = selectedTimeBin.value === idx ? -1 : idx
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
function clearSelection() {
  selectedTimeBin.value = -1; selectedZone.value = null
  selectedAction.value = null; selectedOutcome.value = null
}

// ═══════ Init ═══════
async function init() {
  sankeyState.value = 'loading'
  try {
    await Promise.all([loadSide('left'), loadSide('right')])
    refreshActiveChart()
  } catch (e: any) {
    sankeyError.value = e.message || '加载失败'
    sankeyState.value = 'error'
  }
}

onMounted(async () => {
  // 三分数据
  try { await threeStore.loadAll() } catch {}
  aggData.value = threeStore.aggData
  seasons3p.value = threeStore.seasonList

  // 时间-FG 数据
  try {
    const resp = await fetch('/data/time_fg_base.json')
    useTimeFilterStore().updateCurveData(await resp.json())
  } catch {}

  // 桑基初始加载
  init()
})
</script>

<template>
  <div class="dashboard">
    <div class="col col-left">
      <HexbinPage />
      <TimeFgChart />
    </div>
    <div class="col col-right">
      <KdeChart />
      <ThreePointCompareChart
        v-if="seasons3p.length"
        :aggData="aggData"
        :seasons="seasons3p"
      />
      <!-- ── Sankey section ── -->
      <div class="sankey-panel">
        <!-- Half-court tabs -->
        <div class="court-tabs">
          <button
            :class="['court-tab', { active: sankeySide === 'left' }]"
            @click="sankeySide = 'left'"
          >左半场</button>
          <button
            :class="['court-tab', { active: sankeySide === 'right' }]"
            @click="sankeySide = 'right'"
          >右半场</button>
        </div>

        <!-- Controls -->
        <div class="sankey-controls">
          <div class="control-group">
            <span class="control-label">粒度</span>
            <select
              :value="currentSelection.scope"
              @change="setSelection(sankeySide, { scope: ($event.target as HTMLSelectElement).value as Scope, entityId: undefined })"
              class="sankey-select"
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
              @change="setSelection(sankeySide, { entityId: Number(($event.target as HTMLSelectElement).value) || undefined })"
              class="sankey-select sankey-entity-select"
            >
              <option :value="undefined">-- 请选择 --</option>
              <option v-for="e in entityOptions" :key="e.id" :value="e.id">{{ e.name }}</option>
            </select>
          </div>

          <div class="control-group">
            <span class="control-label">赛季</span>
            <select
              :value="currentSelection.season"
              @change="setSelection(sankeySide, { season: ($event.target as HTMLSelectElement).value })"
              class="sankey-select"
            >
              <option v-for="s in ALL_SEASONS" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
        </div>

        <!-- Breadcrumb -->
        <div
          v-if="selectedTimeBin >= 0 || selectedZone || selectedAction || selectedOutcome"
          class="sankey-breadcrumb"
        >
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
          <button class="clear-all" @click="clearSelection">清除全部</button>
        </div>

        <!-- Chart -->
        <SankeyChart
          :state="sankeyState"
          :nodes="nodes"
          :links="links"
          :selected-time-bin="selectedTimeBin"
          :selected-zone="selectedZone"
          :selected-action="selectedAction"
          :selected-outcome="selectedOutcome"
          @select-time-bin="onSelectTimeBin"
          @select-zone="onSelectZone"
          @select-action="onSelectAction"
          @select-outcome="onSelectOutcome"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  height: calc(100vh - 48px);
  display: grid;
  grid-template-columns: 62fr 38fr;
  gap: 10px;
  padding: 8px 10px;
  box-sizing: border-box;
  overflow-x: hidden;
}

.col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.col-left > :first-child { flex: 1 1 80%; min-height: 0; }
.col-left > :last-child  { flex: 0 0 auto; max-height: 30%; min-height: 0; }

.col::-webkit-scrollbar { width: 4px; }
.col::-webkit-scrollbar-track { background: transparent; }
.col::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

/* ── Sankey panel ── */
.sankey-panel {
  display: flex;
  flex-direction: column;
  flex: 0 0 auto;
}

/* ── Half-court tabs ── */
.court-tabs {
  display: flex;
  gap: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.12);
  align-self: center;
  margin-bottom: 4px;
}
.court-tab {
  padding: 5px 28px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.court-tab:first-child { border-right: 1px solid rgba(255,255,255,0.08); }
.court-tab:hover { background: rgba(255,255,255,0.04); }
.court-tab.active { background: var(--accent-primary); color: #fff; }

/* ── Controls ── */
.sankey-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  flex-wrap: wrap;
  justify-content: center;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.control-label {
  font-size: var(--fs-caption, 11px);
  font-weight: 600;
  color: var(--text-secondary, #8b949e);
  white-space: nowrap;
}

.sankey-select {
  padding: 3px 8px;
  font-size: 12px;
  background: var(--bg-input);
  color: var(--text-primary);
  border: 1px solid var(--border-input);
  border-radius: 6px;
  cursor: pointer;
}
.sankey-select option {
  background: #1a1f2e;
  color: var(--text-primary);
}
.sankey-entity-select {
  min-width: 130px;
  max-width: 160px;
}

/* ── Breadcrumb ── */
.sankey-breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: rgba(52,152,219,0.08);
  border: 1px solid rgba(52,152,219,0.2);
  border-radius: 6px;
  font-size: 11px;
  flex-wrap: wrap;
}
.breadcrumb-label { color: var(--text-secondary); }
.breadcrumb-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 7px;
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
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
.clear-all {
  font-size: 11px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  text-decoration: underline;
}

/* 覆盖 HexbinPage 的全屏样式，适配仪表盘 */
.col-left :deep(.hexbin-page) {
  min-height: 0 !important;
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}
.col-left :deep(.court-container) {
  flex: 1 !important;
  min-height: 0 !important;
}

@media (max-width: 1100px) {
  .dashboard {
    grid-template-columns: 1fr;
    height: auto;
  }
  .col { overflow: visible; }
}
</style>
