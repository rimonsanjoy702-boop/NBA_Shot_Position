<script setup lang="ts">
import SankeyShotFlow from '@/components/SankeyShotFlow.vue'
import HexbinHeatmap from '@/components/HexbinHeatmap.vue'
</script>

<template>
  <div class="page page-structure">
    <div class="two-col">
      <SankeyShotFlow />
      <HexbinHeatmap mode="shot-structure" />
    </div>
  </div>
</template>

<style scoped>
.page { padding: 20px 28px 40px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 1280px) { .two-col { grid-template-columns: 1fr; } }
</style>
