<script setup lang="ts">
import KdePhaseTransition from '@/components/KdePhaseTransition.vue'
import ThreePointAdoption from '@/components/ThreePointAdoption.vue'
</script>

<template>
  <div class="page page-evolution">
    <div class="two-col">
      <KdePhaseTransition />
      <ThreePointAdoption />
    </div>
  </div>
</template>

<style scoped>
.page { padding: 20px 28px 40px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 1280px) { .two-col { grid-template-columns: 1fr; } }
</style>
