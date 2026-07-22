<script setup lang="ts">
import { ref, onMounted } from 'vue'
import HexbinPage from '@/charts/hexbin/HexbinPage.vue'
import KdeChart from '@/charts/kde/KdeChart.vue'
import ThreePointCompareChart from '@/charts/three-point/components/ThreePointCompareChart.vue'
import TimeFgChart from '@/charts/time-fg/TimeFgChart.vue'
import SankeyChart from '@/charts/sankey/SankeyChart.vue'
import { useThreePointCompareStore, type AggDataMap } from '@/charts/three-point/store'
import { useTimeFilterStore } from '@/charts/time-fg/store'
import { fetchSankeySeason, extractSankeyData } from '@/charts/sankey/sankey-data'

// ── 三分数据 ──
const threeStore = useThreePointCompareStore()
const aggData = ref<AggDataMap>({})
const seasons3p = ref<string[]>([])
const showMid = ref(false)

onMounted(async () => {
  // 三分数据
  try { await threeStore.loadAll() } catch {}
  aggData.value = threeStore.aggData
  seasons3p.value = threeStore.seasonList
  showMid.value = threeStore.showMid

  // 时间-FG 数据
  try {
    const resp = await fetch('/data/time_fg_base.json')
    useTimeFilterStore().updateCurveData(await resp.json())
  } catch {}

  // 桑基数据
  try {
    const sankeyData = await fetchSankeySeason('2019-20')
    const { nodes, links } = extractSankeyData(sankeyData, 'league')
    sankeyNodes.value = nodes
    sankeyLinks.value = links
    sankeyState.value = nodes.length > 0 ? 'ready' : 'empty'
  } catch { sankeyState.value = 'empty' }
})

// ── 桑基数据 ──
const sankeyNodes = ref<any[]>([])
const sankeyLinks = ref<any[]>([])
const sankeyState = ref<'loading' | 'ready' | 'empty'>('loading')
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
        :showMid="showMid"
      />
      <SankeyChart
        :state="sankeyState"
        :nodes="sankeyNodes"
        :links="sankeyLinks"
      />
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
