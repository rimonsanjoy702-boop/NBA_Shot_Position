<template>
  <h1>篮球比赛各时段投篮可视化分析</h1>
  <!-- 追加图表组件，页面才会渲染折线图 -->
  <TimeFgChart />
</template>

<script setup lang="ts">
import TimeFgChart from '@/components/TimeFgChart.vue'
import { onMounted } from 'vue'
import { useTimeFilterStore } from '@/store/timeFilter'

const timeStore = useTimeFilterStore()

onMounted(async () => {
  const res = await fetch('/time_fg_base.json')
  const data = await res.json()
  timeStore.updateCurveData(data)
})
</script>

<style scoped>
</style>
