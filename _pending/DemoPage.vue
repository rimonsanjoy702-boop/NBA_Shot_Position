<template>
  <div class=demo-page>

    <div class="chart-container" style="height: 35rem; width: 60rem; background: #00c1">
      <div class="chart-title">
        <div class="chart-name">
          User Connection Sankey Chart By ECharts<br/>
          <span style="font-weight: bold; color: red">Try to click 3rd column!</span>
        </div>
      </div>

      <!-- bind data with v-model -->
      <UserConnectionGraph class="sankey-chart"
                           :stats-nodes="statsNodes" :inter-links="interLinks"
                           v-model:selected-interest="selectedInterest"/>
    </div>

    <div class="chart-container" style="height: 25rem; width: 60rem; background: #0c01">
      <div class="chart-title">
        <div class="chart-name">
          User Distribution Pie Chart By ECharts<br/>
          <span style="font-weight: bold; color: red">Try to click at pies or legends</span>
        </div>
      </div>

      <!-- bind data with prop&event -->
      <UserDistributionPieChart :role-size="roleSize"
                                :selected-interest="selectedInterest"
                                @clickInterest="value => selectedInterest = value"/>

    </div>

    <div class="chart-container" style="width: 60rem; background: #c0c1">
      <div class="chart-title">
        <div class="chart-name">
          Connected Graph By SVG<br/>
          <span style="font-weight: bold; color: red">Try to click nodes!</span>
        </div>
      </div>

      <ConnectionGraph style="height: 400px; width: 800px; margin: 1rem; align-self: center"
                       v-model:selected-interest="selectedInterest"/>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, shallowRef } from 'vue'
import {
  AccountStatsLink,
  AccountStatsNode,
  AccountInterest,
} from '@/models.ts'
import { ElLoading } from 'element-plus'

import { loadRecommendationLinks, loadRecommendationNodes } from "@/data.ts";

import UserConnectionGraph from "@/components/UserConnectionGraph.vue";
import UserDistributionPieChart from "@/components/UserDistributionPieChart.vue";
import ConnectionGraph from "@/components/ConnectionGraph.vue";


const selectedInterest = ref<AccountInterest | null>(null)

const statsNodes = shallowRef<AccountStatsNode[]>([])
const statsLinks = shallowRef<AccountStatsLink[]>([])

const roleSize = shallowRef<Partial<Record<AccountInterest, number>>>({})

const interLinks = computed(() => statsLinks.value.filter(link => {
  const t1 = link.node1.split('/')[0]
  const t2 = link.node2.split('/')[0]
  return t1 != t2 && !(
      (t1 == 'interest' && t2 == 'platform') ||
      (t1 == 'platform' && t2 == 'interest'));
}))

async function init() {
  const loading = ElLoading.service({
    fullscreen: true,
    text: 'loading...',
  })

  const nodes = await loadRecommendationNodes()
  const links = await loadRecommendationLinks()

  // 批量赋值，避免重复渲染
  statsNodes.value = nodes
  statsLinks.value = links

  roleSize.value = Object.fromEntries(
      nodes.filter(node => node.type === 'interest')
          .map(node => [node.key, node.size])
  )

  loading.close()
}

init()

</script>

<style scoped>
.chart-container {
  flex: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 3rem;
}

.chart-title {
  display: flex;
  flex-direction: row;
  justify-content: left;
  align-items: center;
  padding: 1rem;
  gap: 2rem;
}

.chart-name {
  font-size: 1.25rem;
  font-weight: 500;
  line-height: 1.375rem;
}
</style>