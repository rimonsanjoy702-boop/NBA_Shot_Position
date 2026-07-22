<template>
  <div style="width: 100%; height: 520px; margin-top: 20px;">
    <v-echarts :option="chartOpt" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
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

const timeStore = useTimeFilterStore()
const chartOpt = ref<EChartsOption>({})

watch(() => timeStore.timeCurveData, (dataList: TimeShotItem[]) => {
  console.log('原始数据列表', dataList)
  if (!dataList || dataList.length === 0) return

  const xLabels = dataList.map(item => item.label)
  const left2pt = dataList.map(item => item.left_2pt)
  const right2pt = dataList.map(item => item.right_2pt)
  const left3pt = dataList.map(item => item.left_3pt)
  const right3pt = dataList.map(item => item.right_3pt)
  const leftShotCnt = dataList.map(item => item.left_shot_count)
  const rightShotCnt = dataList.map(item => item.right_shot_count)

  console.log('左出手次数数组', leftShotCnt)
  console.log('右出手次数数组', rightShotCnt)

  chartOpt.value = {
    title: {
      text: '各时段左右半场投篮命中率与出手次数',
      left: 'center',
      textStyle: { color: '#e6edf3' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
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
        data: left3pt,
        lineStyle: { type: 'solid', width: 2 },
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#ffb400' }
      },
      {
        name: '右半场三分',
        type: 'line',
        yAxisIndex: 0,
        data: right3pt,
        lineStyle: { type: 'dashed', width: 2 },
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#e63946' }
      },
      {
        name: '左半场出手次数',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: 16,
        data: leftShotCnt
      },
      {
        name: '右半场出手次数',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: 16,
        data: rightShotCnt
      }
    ]
  }
}, { immediate: true })
</script>
