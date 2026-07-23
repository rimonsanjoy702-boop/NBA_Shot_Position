<template>
  <div style="width: 100%; height: 520px; margin-top: 20px;">
    <v-echarts :option="chartOpt" @click="onBinClick" />
  </div>
</template>

<script setup lang="ts">
/**
 * TimeFgChart.vue — 各时段左右半场投篮命中率与出手次数折线+柱状图
 *
 * Type D 联动:
 *   S8 — 点击 bin → Store.setTimeBin → Hexbin 过滤 (通过 Store watch 已就绪)
 *   T1 — 衰减曲线被选 bin 数据点加大 + 保持原色
 *   T2 — 其余 bin 数据点 dim（符号缩小）
 *   T4 — 再次点击同一 bin 取消选中（Store.toggle）
 *
 * Type C 联动 (黄金三角槽同步):
 *   activeSide='left'  → 左半场线条实线/原色，右半场虚线/dim
 *   activeSide='right' → 右半场线条实线/原色，左半场虚线/dim
 */
import { ref, watch } from 'vue'
import { useAnalysisContext } from '@/stores/analysisContext'
import { useTimeFilterStore } from './store'
import type { EChartsOption } from 'echarts'

interface TimeShotItem {
  label: string
  left_2pt: number
  right_2pt: number
  left_3pt: number
  right_3pt: number
  left_shot_count: number
  right_shot_count: number
}

const store = useAnalysisContext()
const timeStore = useTimeFilterStore()
const chartOpt = ref<EChartsOption>({})

// ═══════════════════════════════════════════════════════════
// S8 / T4 — Click handler
// ═══════════════════════════════════════════════════════════

function onBinClick(params: any) {
  // Only handle clicks on series data points (not axis labels, legend, etc.)
  if (params.componentType === 'series' && params.dataIndex !== undefined) {
    store.setTimeBin(params.dataIndex, 'time-fg')
  }
}

// ═══════════════════════════════════════════════════════════
// Chart builder — reacts to data / activeSide / selectedTimeBin
// ═══════════════════════════════════════════════════════════

function buildChart(dataList: TimeShotItem[]) {
  if (!dataList || dataList.length === 0) return

  const bin = store.selectedTimeBin  // null = 全时段, 0-7 = 具体时段
  const side = store.activeSide

  const xLabels = dataList.map(item => item.label)
  const left2pt = dataList.map(item => item.left_2pt)
  const right2pt = dataList.map(item => item.right_2pt)
  const left3pt = dataList.map(item => item.left_3pt)
  const right3pt = dataList.map(item => item.right_3pt)
  const leftShotCnt = dataList.map(item => item.left_shot_count)
  const rightShotCnt = dataList.map(item => item.right_shot_count)

  // ── Per-point symbol sizes for line series (T1/T2) ──
  const defaultSymSize = 6
  const selectedSymSize = 12
  const defaultBarOpacity = 0.15
  const selectedBarOpacity = 0.4

  chartOpt.value = {
    title: {
      text: '各时段左右半场投篮命中率与出手次数',
      left: 'center',
      textStyle: { color: '#e6edf3' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: [
        '左半场两分',
        '右半场两分',
        '左半场三分',
        '右半场三分',
        '左半场出手次数',
        '右半场出手次数'
      ],
      top: 30,
      textStyle: { color: '#8b949e' }
    },
    xAxis: {
      type: 'category',
      data: xLabels
    },
    yAxis: [
      {
        name: '命中率(%)',
        type: 'value',
        min: 30,
        max: 65
      },
      {
        name: '出手次数',
        type: 'value',
        min: 0,
        alignTicks: true
      }
    ],
    series: [
      // ── Left 2PT ──
      {
        name: '左半场两分',
        type: 'line',
        yAxisIndex: 0,
        data: left2pt.map((v, i) => ({
          value: v,
          symbolSize: bin != null && i === bin ? selectedSymSize : defaultSymSize,
          itemStyle: {
            borderColor: bin != null && i === bin ? '#fff' : undefined,
            borderWidth: bin != null && i === bin ? 2 : 0,
          },
        })),
        lineStyle: {
          color: side === 'left' ? '#5470C6' : '#888',
          width: side === 'left' ? 2 : 1,
          type: side === 'left' ? 'solid' : 'dashed',
        },
        itemStyle: { color: side === 'left' ? '#5470C6' : '#888' },
      },
      // ── Right 2PT ──
      {
        name: '右半场两分',
        type: 'line',
        yAxisIndex: 0,
        data: right2pt.map((v, i) => ({
          value: v,
          symbolSize: bin != null && i === bin ? selectedSymSize : defaultSymSize,
          itemStyle: {
            borderColor: bin != null && i === bin ? '#fff' : undefined,
            borderWidth: bin != null && i === bin ? 2 : 0,
          },
        })),
        lineStyle: {
          color: side === 'right' ? '#5470C6' : '#888',
          width: side === 'right' ? 2 : 1,
          type: side === 'right' ? 'solid' : 'dashed',
        },
        itemStyle: { color: side === 'right' ? '#5470C6' : '#888' },
      },
      // ── Left 3PT ──
      {
        name: '左半场三分',
        type: 'line',
        yAxisIndex: 0,
        data: left3pt.map((v, i) => ({
          value: v,
          symbolSize: bin != null && i === bin ? selectedSymSize : defaultSymSize,
          itemStyle: {
            borderColor: bin != null && i === bin ? '#fff' : undefined,
            borderWidth: bin != null && i === bin ? 2 : 0,
          },
        })),
        lineStyle: {
          color: side === 'left' ? '#ffb400' : '#888',
          width: side === 'left' ? 2 : 1,
        },
        itemStyle: { color: side === 'left' ? '#ffb400' : '#888' },
      },
      // ── Right 3PT ──
      {
        name: '右半场三分',
        type: 'line',
        yAxisIndex: 0,
        data: right3pt.map((v, i) => ({
          value: v,
          symbolSize: bin != null && i === bin ? selectedSymSize : defaultSymSize,
          itemStyle: {
            borderColor: bin != null && i === bin ? '#fff' : undefined,
            borderWidth: bin != null && i === bin ? 2 : 0,
          },
        })),
        lineStyle: {
          color: side === 'right' ? '#e63946' : '#888',
          width: side === 'right' ? 2 : 1,
          type: side === 'right' ? 'solid' : 'dashed',
        },
        itemStyle: { color: side === 'right' ? '#e63946' : '#888' },
      },
      // ── Left shot count bars ──
      {
        name: '左半场出手次数',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: 16,
        data: leftShotCnt.map((v, i) => ({
          value: v,
          itemStyle: {
            opacity: bin == null ? defaultBarOpacity : (i === bin ? selectedBarOpacity : 0.05),
            color: side === 'left' ? '#5470C6' : '#888',
          },
        })),
      },
      // ── Right shot count bars ──
      {
        name: '右半场出手次数',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: 16,
        data: rightShotCnt.map((v, i) => ({
          value: v,
          itemStyle: {
            opacity: bin == null ? defaultBarOpacity : (i === bin ? selectedBarOpacity : 0.05),
            color: side === 'right' ? '#91cc75' : '#888',
          },
        })),
      },
    ],
  }
}

// ═══════════════════════════════════════════════════════════
// Reactivity — rebuild chart when data, activeSide, or timeBin changes
// ═══════════════════════════════════════════════════════════

watch(() => timeStore.timeCurveData, (dataList: TimeShotItem[]) => {
  buildChart(dataList)
}, { immediate: true })

watch(() => store.activeSide, () => {
  buildChart(timeStore.timeCurveData)
})

watch(() => store.selectedTimeBin, () => {
  buildChart(timeStore.timeCurveData)
})
</script>
