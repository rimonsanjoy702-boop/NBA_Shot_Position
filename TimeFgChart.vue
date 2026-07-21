<template>
  <div style="width: 100%; height: 520px; margin-top: 20px;">
    <v-echarts :option="chartOpt" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useTimeFilterStore } from '@/store/timeFilter'
import type { EChartsOption } from 'echarts'

interface TimeShotItem {
  time_bin: number
  label: string
  left_2pt: number
  right_2pt: number
  left_3pt: number
  right_3pt: number
  shot_count: number
  avg_fg: number
  all_made: number
  all_total: number
}

const timeStore = useTimeFilterStore()
const chartOpt = ref<EChartsOption>({})

watch(() => timeStore.timeCurveData, (dataList: TimeShotItem[]) => {
  if (!dataList || dataList.length === 0) return

  const xLabels = dataList.map(item => item.label)
  const left2pt = dataList.map(item => item.left_2pt)
  const right2pt = dataList.map(item => item.right_2pt)
  const left3pt = dataList.map(item => item.left_3pt)
  const right3pt = dataList.map(item => item.right_3pt)
  const shotCount = dataList.map(item => item.shot_count)

  chartOpt.value = {
    title: {
      text: '各时段左右半场投篮命中率与出手次数',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['左半场两分', '右半场两分', '左半场三分', '右半场三分', '总出手次数'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: xLabels
    },
    yAxis: [
      {
        name: '命中率(%)',
        type: 'value',
        min: 0,
        max: 65
      },
      {
        name: '出手次数',
        type: 'value',
        min: 0,
        axisLabel: { formatter: '{value} 次' }
      }
    ],
    series: [
      {
        name: '左半场两分',
        type: 'line',
        yAxisIndex: 0,
        data: left2pt
      },
      {
        name: '右半场两分',
        type: 'line',
        yAxisIndex: 0,
        data: right2pt
      },
      {
        name: '左半场三分',
        type: 'line',
        yAxisIndex: 0,
        data: left3pt
      },
      {
        name: '右半场三分',
        type: 'line',
        yAxisIndex: 0,
        data: right3pt
      },
      {
        name: '总出手次数',
        type: 'bar',
        yAxisIndex: 1, // 绑定右侧坐标轴
        data: shotCount
      }
    ]
  }
}, { immediate: true })
</script>
