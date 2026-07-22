<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { useAnalysisContext } from '@/stores/analysisContext'
import { nbaColors } from '@/util/colors'

const store = useAnalysisContext()
const props = defineProps<{ mode: 'space-explorer' | 'shot-structure' }>()

// ── Mock hexbin data ──
interface HexCell { x: number; y: number; count: number; fg_pct: number; zone: string }
const hexData = ref<HexCell[]>([])
const loading = ref(false)

const ZONES = ['Restricted Area','In The Paint (Non-RA)','Mid-Range','Left Corner 3','Right Corner 3','Above the Break 3','Backcourt']
const ZONE_COLORS: Record<string,string> = {
  'Restricted Area': nbaColors.rim,
  'In The Paint (Non-RA)': nbaColors.twoPT,
  'Mid-Range': nbaColors.midRange,
  'Left Corner 3': nbaColors.threePT,
  'Right Corner 3': nbaColors.threePT,
  'Above the Break 3': nbaColors.threePT,
  'Backcourt': '#666',
}

function generateMockHex() {
  const cells: HexCell[] = []
  for (let i = 0; i < 200; i++) {
    const x = (Math.random() - 0.5) * 500
    const y = Math.random() * 400
    let zone: string
    const dist = Math.sqrt(x*x + y*y)
    if (dist < 30) zone = 'Restricted Area'
    else if (dist < 80) zone = 'In The Paint (Non-RA)'
    else if (dist < 180) zone = 'Mid-Range'
    else if (x < -60 && dist > 200) zone = 'Left Corner 3'
    else if (x > 60 && dist > 200) zone = 'Right Corner 3'
    else if (dist > 200) zone = 'Above the Break 3'
    else zone = 'Backcourt'
    cells.push({ x, y, count: Math.floor(Math.random()*500+10), fg_pct: 0.3+Math.random()*0.4, zone })
  }
  hexData.value = cells
}

onMounted(() => { generateMockHex(); loading.value = false })

// ── Filter by store state ──
const filteredHex = computed(() => {
  let data = hexData.value
  if (props.mode === 'shot-structure' && store.selectedShotType) {
    const bias = store.selectedShotType === '3PT' ? 0.7 : -0.7
    data = data.filter(() => Math.random() > bias)
  }
  if (store.selectedZone) {
    data = data.map(h => ({...h, fg_pct: h.zone === store.selectedZone ? h.fg_pct : h.fg_pct*0.3, count: h.zone === store.selectedZone ? h.count : h.count*0.2 }))
  }
  return data
})

// ── ECharts option ──
const hexOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item' as const,
    backgroundColor: 'rgba(13,17,23,0.95)',
    borderColor: 'rgba(255,255,255,0.1)',
    textStyle: { color: '#e6edf3', fontSize: 13 },
    formatter: (p: any) => {
      const h = filteredHex.value[p.dataIndex]
      if (!h) return ''
      return `<b>${h.zone}</b><br/>命中率: ${(h.fg_pct*100).toFixed(1)}%<br/>出手: ${h.count}次`
    }
  },
  grid: { left: 40, right: 40, top: 20, bottom: 20 },
  xAxis: { type: 'value' as const, min: -250, max: 250, show: false },
  yAxis: { type: 'value' as const, min: -52, max: 400, show: false },
  series: [{
    type: 'scatter' as const,
    data: filteredHex.value.map(h => ({
      value: [h.x, h.y],
      symbolSize: Math.max(8, Math.sqrt(h.count) * 1.2),
      itemStyle: {
        color: ZONE_COLORS[h.zone] || '#666',
        opacity: 0.2 + (h.fg_pct - 0.3) * 1.2,
        borderColor: store.selectedZone === h.zone ? '#fff' : 'transparent',
        borderWidth: store.selectedZone === h.zone ? 2 : 0,
      }
    })),
    emphasis: { itemStyle: { opacity: 1, borderColor: '#fff', borderWidth: 2 } },
    animation: true, animationDuration: 400,
  }],
}))

watch(() => [store.selectedSeason, store.selectedTeamId, store.selectedTimeBin, store.selectedZone, store.selectedShotType], () => {
  generateMockHex()
}, { deep: false })
</script>

<template>
  <div class="hexbin-container">
    <div class="hex-header">
      <span class="hex-title">
        {{ mode === 'space-explorer' ? '全场投篮热力图' : '投篮空间分布' }}
      </span>
      <span class="hex-meta">
        {{ store.selectedSeason }} · {{ store.entityLabel.text }}
        <span v-if="store.selectedTimeBin !== null" class="time-badge">Q{{Math.floor((store.selectedTimeBin??0)/2)+1}}{{ (store.selectedTimeBin??0)%2===0?'前':'后' }}</span>
        <span v-if="store.selectedShotType" class="type-badge">{{ store.selectedShotType }}</span>
      </span>
    </div>
    <div class="hex-chart-area">
      <v-chart :option="hexOption" autoresize style="width:100%;height:100%" />
      <div class="court-overlay">
        <svg viewBox="0 0 500 400" class="court-svg">
          <rect x="0" y="0" width="500" height="400" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="2"/>
          <line x1="250" y1="0" x2="250" y2="400" stroke="rgba(255,255,255,0.06)" stroke-width="1" stroke-dasharray="8,4"/>
          <circle cx="250" cy="25" r="6" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
          <circle cx="250" cy="375" r="6" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
        </svg>
      </div>
    </div>
    <div class="hex-footer">
      <div class="legend-item"><span class="dot" style="background:#ff6b6b"></span>禁区</div>
      <div class="legend-item"><span class="dot" style="background:#f39c12"></span>两分</div>
      <div class="legend-item"><span class="dot" style="background:#8b949e"></span>中距离</div>
      <div class="legend-item"><span class="dot" style="background:#3498db"></span>三分</div>
      <div class="legend-scale">气泡大小=出手量 · 透明度=命中率</div>
    </div>
  </div>
</template>

<style scoped>
.hexbin-container {
  position: relative;
  display: flex; flex-direction: column;
  height: 100%;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 10px;
  padding: 14px 16px 8px;
  width: 100%;
  box-sizing: border-box;
}
.hex-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.hex-title { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.hex-meta { font-size: 12px; color: var(--text-secondary); display: flex; gap: 8px; align-items: center; }
.time-badge { background: rgba(255,107,107,0.15); color: #ff6b6b; padding: 1px 8px; border-radius: 4px; font-size: 11px; }
.type-badge { background: rgba(52,152,219,0.15); color: #3498db; padding: 1px 8px; border-radius: 4px; font-size: 11px; }
.hex-chart-area {
  flex: 1; min-height: 0;
  position: relative;
}
.court-overlay {
  position: absolute; inset: 0;
  pointer-events: none; z-index: 1;
}
.court-svg { width: 100%; height: 100%; opacity: 0.4; }
.hex-footer { display: flex; gap: 16px; align-items: center; padding: 6px 0 0; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--text-secondary); }
.dot { width: 8px; height: 8px; border-radius: 2px; }
.legend-scale { margin-left: auto; font-size: 10px; color: var(--text-tertiary); }
</style>
