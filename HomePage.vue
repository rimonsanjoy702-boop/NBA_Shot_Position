<template>
  <div class="home-container">
    <div class="content-box">
      <h1>NBA投篮距离双峰相变可视化系统</h1>
      <p class="desc">基于1997-2020完整常规赛投篮数据 · KDE核密度演化分析</p>

      <!-- 图表组件直接嵌入首页 -->
      <KdeChart />
    </div>
  </div>
</template>

<script setup>
// 导入图表组件
import KdeChart from "@/components/KdeChart.vue"
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #ffffff;
  color: #1f2937;
  padding: 30px 20px;
  box-sizing: border-box;
}
.content-box {
  max-width: 1300px;
  margin: 0 auto;
}
h1 {
  font-size: 32px;
  margin: 0 0 12px;
  color: #111827;
}
.desc {
  color: #6b7280;
  font-size: 16px;
  margin-bottom: 30px;
}
</style>
