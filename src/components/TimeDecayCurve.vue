<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import VChart from 'vue-echarts'
import { useAnalysisContext } from '@/stores/analysisContext'
import { nbaColors } from '@/util/colors'

const store = useAnalysisContext()

// ── Mock time-decay data ──
interface TimeBin { label: string; fg_pct: number; fg2_pct: number; fg3_pct: number; total_shots: number }
const bins = ref<TimeBin[]>([])

const BIN_LABELS = ['Q1前','Q1后','Q2前','Q2后','Q3前','Q3后','Q4前','Q4后']
function generateMockBins() {
  const base: TimeBin[] = [
    { label:'Q1前', fg_pct:46.9, fg2_pct:48.9, fg3_pct:38.5, total_shots:615335 },
    { label:'Q1后', fg_pct:46.3, fg2_pct:48.9, fg3_pct:37.0, total_shots:608162 },
    { label:'Q2前', fg_pct:44.7, fg2_pct:47.6, fg3_pct:34.8, total_shots:588579 },
    { label:'Q2后', fg_pct:46.3, fg2_pct:49.3, fg3_pct:36.3, total_shots:590400 },
    { label:'Q3前', fg_pct:45.4, fg2_pct:48.2, fg3_pct:36.1, total_shots:587794 },
    { label:'Q3后', fg_pct:44.8, fg2_pct:47.8, fg3_pct:35.9, total_shots:569456 },
    { label:'Q4前', fg_pct:43.5, fg2_pct:46.9, fg3_pct:34.1, total_shots:556445 },
    { label:'Q4后', fg_pct:43.7, fg2_pct:47.8, fg3_pct:33.4, total_shots:572338 },
  ]
  bins.value = base.map(b => ({...b, fg_pct: b.fg_pct + (Math.random()-0.5)*2, fg2_pct: b.fg2_pct + (Math.random()-0.5)*2, fg3_pct: b.fg3_pct + (Math.random()-0.5)*2 }))
}
generateMockBins()

// ── Click handler ──
function onClick(params: any) {
  if (params.componentType === 'series') {
    const idx = params.dataIndex
    if (store.selectedTimeBin === idx) {
      store.setTimeBin(null, 'decay')
    } else {
      store.setTimeBin(idx, 'decay')
    }
  }
}

// ── ECharts option ──
const decayOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis' as const,
    backgroundColor: 'rgba(13,17,23,0.95)',
    borderColor: 'rgba(255,255,255,0.1)',
    textStyle: { color: '#e6edf3', fontSize: 13 },
    formatter: (params: any) => {
      const b = bins.value[params[0]?.dataIndex]
      if (!b) return ''
      return `<b>${b.label}</b><br/>FG%: <b>${b.fg_pct.toFixed(1)}%</b><br/>2PT: ${b.fg2_pct.toFixed(1)}% | 3PT: ${b.fg3_pct.toFixed(1)}%<br/>出手: ${(b.total_shots/1000).toFixed(0)}K`
    }
  },
  legend: { data: ['2PT FG%','3PT FG%'], bottom: 4, textStyle: { color: '#8b949e', fontSize: 11 }, itemWidth: 10, itemHeight: 8 },
  grid: { left: 44, right: 48, top: 16, bottom: 32 },
  xAxis: {
    type: 'category' as const, data: bins.value.map(b => b.label),
    axisLabel: { color: '#8b949e', fontSize: 11 },
    axisTick: { show: false },
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
  },
  yAxis: [{
    type: 'value' as const, name: 'FG%', min: 28, max: 55,
    axisLabel: { color: '#8b949e', fontSize: 11, formatter: '{value}%' },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
  }, {
    type: 'value' as const, name: '出手数', show: false,
  }],
  series: [
    {
      name: '2PT FG%', type: 'line', smooth: true,
      data: bins.value.map(b => b.fg2_pct),
      lineStyle: { color: nbaColors.twoPT, width: 2.5 },
      itemStyle: { color: nbaColors.twoPT },
      symbol: 'circle', symbolSize: 6,
      markLine: store.selectedTimeBin !== null ? {
        silent: true, symbol: 'none',
        lineStyle: { color: '#fff', type: 'dashed', width: 1.5 },
        data: [{ xAxis: store.selectedTimeBin ?? 0 }]
      } : undefined,
    },
    {
      name: '3PT FG%', type: 'line', smooth: true,
      data: bins.value.map(b => b.fg3_pct),
      lineStyle: { color: nbaColors.threePTLine, width: 2.5 },
      itemStyle: { color: nbaColors.threePTLine },
      symbol: 'diamond', symbolSize: 6,
    },
    {
      name: '出手量', type: 'bar', yAxisIndex: 1,
      data: bins.value.map(b => b.total_shots),
      itemStyle: { color: 'rgba(255,255,255,0.06)' },
      barWidth: '60%',
    },
  ],
}))

watch(() => store.selectedSeason, () => { generateMockBins() })
</script>

<template>
  <div class="decay-container">
    <div class="decay-header">
      <span class="decay-title">⏱ 时间-FG% 衰减曲线</span>
      <div class="decay-controls">
        <button
          :class="['mode-btn', { active: store.timeLinkMode === 'sync' }]"
          @click="store.timeLinkMode = 'sync'"
        >同步</button>
        <button
          :class="['mode-btn', { active: store.timeLinkMode === 'independent' }]"
          @click="store.timeLinkMode = 'independent'"
        >分开</button>
        <button v-if="store.selectedTimeBin !== null" class="clear-btn" @click="store.setTimeBin(null, 'decay')">清除</button>
      </div>
    </div>
    <v-chart :option="decayOption" autoresize style="width:100%;height:200px" @click="onClick" />
    <div class="decay-hint">💡 点击时间 bin → Hexbin 过滤到该时段 | 再次点击取消</div>
  </div>
</template>

<style scoped>
.decay-container {
  background: var(--bg-card); border: 1px solid var(--border-card); border-radius: 10px;
  padding: 14px 16px 8px; margin-bottom: 4px;
}
.decay-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.decay-title { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.decay-controls { display: flex; gap: 6px; }
.mode-btn {
  padding: 3px 12px; border-radius: 5px; border: 1px solid var(--border-input);
  background: transparent; color: var(--text-secondary); font-size: 11px; cursor: pointer;
}
.mode-btn.active { background: rgba(52,152,219,0.2); border-color: var(--border-active); color: var(--accent-primary); }
.clear-btn {
  padding: 3px 10px; border-radius: 5px; border: 1px solid rgba(255,107,107,0.3);
  background: transparent; color: var(--semantic-missed); font-size: 11px; cursor: pointer;
}
.decay-hint { text-align: center; color: var(--text-tertiary); font-size: 10px; padding: 4px 0 0; }
</style>
