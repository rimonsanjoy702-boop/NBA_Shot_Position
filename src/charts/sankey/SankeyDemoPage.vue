<script setup lang="ts">
/**
 * SankeyDemoPage.vue — Minimal demo page for the sankey chart.
 *
 * Features:
 *   - Season selector (23 seasons)
 *   - Court side selector (all / left / right)
 *   - Scope selector (league only for now; team/player later)
 *   - SankeyChart component with L1 click handling
 */

import { ref, computed, watch } from 'vue'
import { fetchSankeySeason, extractSankeyData } from './sankey-data'
import type { SankeySeasonData, SankeyNode, SankeyLink, LoadingState, CourtSide, Scope } from './types'
import { ALL_SEASONS } from './types'
import SankeyChart from './SankeyChart.vue'

// ============================================================================
// State
// ============================================================================

const season = ref('2014-15')
const courtSide = ref<CourtSide>('all')
const scope = ref<Scope>('league')
const entityId = ref<number | undefined>(undefined)

const loadingState = ref<LoadingState>('loading')
const errorMessage = ref('')

const seasonData = ref<SankeySeasonData | null>(null)
const nodes = ref<SankeyNode[]>([])
const links = ref<SankeyLink[]>([])

// Interaction state by layer
const selectedTimeBin = ref<number>(-1)
const selectedZone = ref<string | null>(null)
const selectedAction = ref<string | null>(null)
const selectedOutcome = ref<string | null>(null)

// ============================================================================
// Title
// ============================================================================

const title = computed(() => {
  let t = `投篮结构 · ${season.value}`
  if (scope.value === 'league') t += ' · 联盟'
  else if (scope.value === 'team') t += ' · 球队'
  else t += ' · 球员'
  return t
})

// ============================================================================
// Data loading
// ============================================================================

async function loadData() {
  loadingState.value = 'loading'
  errorMessage.value = ''
  try {
    seasonData.value = await fetchSankeySeason(season.value)
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
watch(scope, () => { refreshExtraction() })

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
      <!-- Court side -->
      <div class="control-group">
        <span class="control-label">半场</span>
        <div class="side-tabs">
          <button
            v-for="s in (['all','left','right'] as const)"
            :key="s"
            :class="['side-tab', { active: courtSide === s }]"
            @click="courtSide = s"
          >
            {{ s === 'all' ? '全部' : s === 'left' ? '左半场' : '右半场' }}
          </button>
        </div>
      </div>

      <!-- Season -->
      <div class="control-group">
        <span class="control-label">赛季</span>
        <select v-model="season" class="season-select">
          <option v-for="s in ALL_SEASONS" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <!-- Scope -->
      <div class="control-group">
        <span class="control-label">粒度</span>
        <div class="side-tabs">
          <button
            v-for="sc in (['league','team','player'] as const)"
            :key="sc"
            :class="['side-tab', { active: scope === sc }]"
            @click="scope = sc"
          >
            {{ sc === 'league' ? '联盟' : sc === 'team' ? '球队' : '球员' }}
          </button>
        </div>
        <span v-if="scope !== 'league'" class="wip-badge">即将支持</span>
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
      <button class="clear-all" @click="selectedTimeBin = -1; selectedZone = null; selectedAction = null; selectedOutcome = null">
        清除全部
      </button>
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

    <!-- Stats summary -->
    <div v-if="loadingState === 'ready'" class="stats-row">
      <div class="stat-card">
        <div class="stat-num">{{ nodes.filter(n => n.layer===2).reduce((s,n)=>s+n.size,0).toLocaleString() }}</div>
        <div class="stat-label">总出手</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">
          {{ (() => { const m = nodes.find(n=>n.id==='L4_Made'); const t = nodes.find(n=>n.id==='L4_Missed'); const total = (m?.size||0)+(t?.size||0); return total>0 ? ((m?.size||0)/total*100).toFixed(1)+'%' : '--' })() }}
        </div>
        <div class="stat-label">总命中率</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ links.length }}</div>
        <div class="stat-label">有效路径</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ nodes.length }}</div>
        <div class="stat-label">活跃节点</div>
      </div>
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

/* Season select */
.season-select {
  padding: 4px 8px;
  font-size: 12px;
  background: rgba(255,255,255,0.06);
  color: #e6edf3;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 6px;
  cursor: pointer;
}
.season-select option {
  background: #1a1f2e;
  color: #e6edf3;
}

.wip-badge {
  font-size: 10px;
  color: #f9c74f;
  background: rgba(249,199,79,0.12);
  padding: 2px 6px;
  border-radius: 4px;
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
.time-chip { background: #e63946; }
.zone-chip { background: #43aa8b; }
.action-chip { background: #A0A4A8; }
.outcome-chip { background: #3498db; }

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

/* ===== Stats row ===== */
.stats-row {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.stat-card {
  text-align: center;
  padding: 12px 24px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
}

.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: #e6edf3;
}

.stat-label {
  font-size: 11px;
  color: #8b949e;
  margin-top: 2px;
}
</style>
