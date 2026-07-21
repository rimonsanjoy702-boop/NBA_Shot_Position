<script setup lang="ts">
import { AccountInterest, accountInterests, AccountStatsNode } from "@/models.ts";
import VChart from "vue-echarts";
import { computed } from "vue";
import { interestColorMap } from "@/util/colors.ts";

const props = defineProps<{
  roleSize: Partial<Record<AccountInterest, number>>
  selectedInterest: AccountInterest | null
}>()

const emit = defineEmits<{
  (e: 'clickInterest', interest: AccountInterest | null): void
}>()

const totalSize = computed(() => {
  return Object.values(props.roleSize).reduce((acc, size) => acc + (size ?? 0), 0)
})

function getOption() {
  if (!totalSize.value) return {}
  return {
    tooltip: {
      trigger: 'item'
    },
    series: [{
      type: 'pie',
      radius: ['50%', '100%'],
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 3,
      },
      labelLine: {
        show: false,
      },
      label: {
        show: false,
      },
      data: accountInterests.map(role => ({
        name: role,
        value: props.roleSize[role] ?? 0,
        itemStyle: {
          color: interestColorMap[role],
        },
      }))
    }]
  }
}

function formatBignum(x: number) {
  if (x > 1000) {
    return (x / 1000).toFixed(1) + 'K'
  }
  return x.toFixed(0)
}

function onChartClick(params: any) {
  if (params.componentType == "series") {
    emit('clickInterest', params.name === props.selectedInterest ? null : params.name);
  }
}

function onLegendClick(role: AccountInterest) {
  if (role === props.selectedInterest) {
    emit('clickInterest', null);
  } else {
    emit('clickInterest', role);
  }
}

</script>

<template>
  <div class="container">
    <div class="chart">
      <v-chart :option="getOption()" autoresize @mouseup="onChartClick"
               style="width: 100%; height: 100%"/>
    </div>
    <div class="legend">
      <div v-for="role in accountInterests" :key="role"
           style="cursor: pointer"
           @click="onLegendClick(role)">

        <div v-if="role == selectedInterest" style="font-weight: bold; color: red;">
          Selected!!
        </div>

        <div>
          {{ role }}<br/>
          {{ formatBignum(roleSize[role] ?? 0) }}/{{ formatBignum(totalSize) }}
        </div>

        <div class="dot" :style="{background: interestColorMap[role]}"/>
      </div>
    </div>

  </div>
</template>

<style scoped>
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem 2rem;
  gap: 1rem;
}

.chart {
  width: 20rem;
  height: 100%;
}

.legend {
  width: 20rem;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-auto-rows: 2rem;
  gap: 1rem;

  div {
    display: flex;
    justify-content: end;
    align-items: center;
    text-align: right;
    color: #4E5969;
    font-size: 0.75rem;
    font-weight: 400;
    line-height: normal;
    gap: 0.75rem;
  }

  .dot {
    flex: none;
    width: 1.625rem;
    height: 1.625rem;
    border-radius: 9999rem;
  }
}
</style>