<script setup lang="ts">
import HexbinHeatmap from '@/components/HexbinHeatmap.vue'
import TimeDecayCurve from '@/components/TimeDecayCurve.vue'
</script>

<template>
  <div class="page page-space">
    <TimeDecayCurve />
    <HexbinHeatmap mode="space-explorer" />
  </div>
</template>

<style scoped>
.page { padding: 20px 28px 40px; }
.page-space { display: flex; flex-direction: column; gap: 4px; }
</style>
