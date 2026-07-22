<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import VChart from 'vue-echarts'
import { useAnalysisContext } from '@/stores/analysisContext'
import { nbaColors } from '@/util/colors'

const store = useAnalysisContext()

// ── Mock data ──
interface TeamYear { season: string; year: number; avg_3par: number; avg_win_pct: number }
interface GroupLine { group: string; color: string; data: TeamYear[] }

const groups = ref<GroupLine[]>([])
function generateMockGroups() {
  const seasons = []
  for (let y=1998; y<=2020; y++) seasons.push({ season: `${y-1}-${String(y).slice(-2)}`, year: y })
  const leader = seasons.map(s => ({...s, avg_3par: 0.12 + (s.year-1998)/22*0.28 + (s.year>=2012?(s.year-2012)*0.015:0) + Math.random()*0.02, avg_win_pct: 0.45 + Math.random()*0.2 }))
  const laggard = seasons.map(s => ({...s, avg_3par: 0.12 + (s.year-1998)/22*0.22 + (s.year>=2018?(s.year-2018)*0.02:0) + Math.random()*0.02, avg_win_pct: 0.40 + Math.random()*0.2 }))
  const mid = seasons.map(s => ({...s, avg_3par: 0.12 + (s.year-1998)/22*0.25 + Math.random()*0.02, avg_win_pct: 0.42 + Math.random()*0.2 }))
  groups.value = [
    { group: '先行者 (14队)', color: nbaColors.leader, data: leader },
    { group: '落后者 (19队)', color: nbaColors.laggard, data: laggard },
    { group: '过渡组 (4队)', color: nbaColors.mid, data: mid },
  ]
}
generateMockGroups()

const adoptionOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'axis' as const, backgroundColor: 'rgba(13,17,23,0.95)', borderColor: 'rgba(255,255,255,0.1)', textStyle: { color: '#e6edf3', fontSize: 13 } },
  legend: { data: groups.value.map(g=>g.group), bottom: 4, textStyle: { color: '#8b949e', fontSize: 11 } },
  grid: { left: 48, right: 48, top: 16, bottom: 36 },
  xAxis: { type: 'category' as const, data: groups.value[0]?.data.map(d=>d.year)||[], axisLabel: { color: '#8b949e', fontSize: 10, interval: 2 }, name: '赛季', nameTextStyle: { color: '#8b949e', fontSize: 11 } },
  yAxis: [
    { type: 'value' as const, name: '三分出手占比', min: 0, max: 0.55, axisLabel: { color: '#8b949e', fontSize: 10, formatter: (v:number)=>(v*100).toFixed(0)+'%' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
    { type: 'value' as const, name: '胜率', min: 0.3, max: 0.7, axisLabel: { color: '#8b949e', fontSize: 10, formatter: (v:number)=>(v*100).toFixed(0)+'%' }, splitLine: { show: false } },
  ],
  series: [
    ...groups.value.map(g => ({
      name: g.group, type: 'line' as const, yAxisIndex: 0,
      data: g.data.map(d => d.avg_3par),
      lineStyle: { color: g.color, width: g.group.includes('先行')?3:g.group.includes('过渡')?1.5:2, type: g.group.includes('落后')?'dashed' as const:'solid' as const },
      symbol: 'none' as const, smooth: true,
    })),
    ...groups.value.filter(g=>!g.group.includes('过渡')).map(g => ({
      name: g.group+'胜率', type: 'line' as const, yAxisIndex: 1,
      data: g.data.map(d => d.avg_win_pct),
      lineStyle: { color: g.color, width: 1, opacity: 0.35, type: 'dotted' as const },
      symbol: 'none' as const, smooth: true,
    })),
  ],
}))

watch(() => store.selectedSeason, () => {})
</script>

<template>
  <div class="adoption-container">
    <div class="adoption-header">
      <span class="adoption-title">📈 三分转型分层 — 37支球队三类分化</span>
      <span class="adoption-hint">实线=三分出手占比 | 虚线=常规赛胜率</span>
    </div>
    <v-chart :option="adoptionOption" autoresize style="width:100%;height:320px" />
    <div class="adoption-summary">
      <div class="group-card leader">
        <span class="group-dot" style="background:#00d2a0"></span>
        <span class="group-name">先行者 14队</span>
        <span class="group-detail">拐点: 2012-14</span>
        <span class="group-detail">胜率: ~58%</span>
      </div>
      <div class="group-card mid">
        <span class="group-dot" style="background:#f4d03f"></span>
        <span class="group-name">过渡组 4队</span>
        <span class="group-detail">拐点: 2015-17</span>
      </div>
      <div class="group-card laggard">
        <span class="group-dot" style="background:#8b949e"></span>
        <span class="group-name">落后者 19队</span>
        <span class="group-detail">拐点: 2018+</span>
        <span class="group-detail">胜率: ~51%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.adoption-container { background: var(--bg-card); border: 1px solid var(--border-card); border-radius: 10px; padding: 14px 16px 8px; }
.adoption-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.adoption-title { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.adoption-hint { font-size: 11px; color: var(--text-tertiary); }
.adoption-summary { display: flex; gap: 8px; margin-top: 6px; }
.group-card { flex: 1; display: flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 6px; background: rgba(255,255,255,0.03); font-size: 11px; }
.group-dot { width: 8px; height: 8px; border-radius: 50%; }
.group-name { color: var(--text-primary); font-weight: 600; }
.group-detail { color: var(--text-secondary); }
</style>
