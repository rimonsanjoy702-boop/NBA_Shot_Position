<script setup lang="ts">
import VChart from "vue-echarts";
import { AccountInterest, AccountStatsLink, AccountStatsNode } from "@/models.ts";
import { ref, watchEffect } from "vue";

const props = defineProps<{
  statsNodes: AccountStatsNode[]
  interLinks: AccountStatsLink[]
}>()

const selectedInterest = defineModel<AccountInterest | null>('selectedInterest', {required: true})

const hoveredINterest = ref<AccountInterest | null>(null)

interface ChartNode {
  id: string
  name: string
  type: AccountStatsNode['type']
  size: number
}

interface ChartLink {
  source: string
  source_node: ChartNode
  target: string
  target_node: ChartNode
  value: number
}

const ColumnIdx: Record<AccountStatsNode['type'], number> = {
  'platform': 0,
  'role': 1,
  'interest': 2,
}

function formatTooltip(params: { name: string; data: any, dataType: string }) {
  if (params.dataType != 'node') {
    const key1 = params.data.source?.split('/')?.[1];
    const key2 = params.data.target?.split('/')?.[1];
    return `${key1} - ${key2}：cnt=${params.data.value}`;
  }
  return `${params.name}：${params.data.size}人`;
}

function renderSankeyChart() {

  const nodes = props.statsNodes.map((node) => ({
    id: node.id,
    name: node.key,
    depth: ColumnIdx[node.type],
    type: node.type,
    size: node.size,
    itemStyle: {
      color: node.type === 'interest' ? (node.key == selectedInterest.value ? '#165DFF' : '#97b2ff') : '#C9CDD4',
    },
  }))

  const nodeMap = Object.fromEntries(nodes.map((node) => [node.id, node]))

  // 转换链接数据
  const links = props.interLinks.map((link) => ({
    source: link.node1,
    source_node: nodeMap[link.node1],
    target: link.node2,
    target_node: nodeMap[link.node2],
    value: link.size,
  }))

  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    series: [
      {
        type: 'sankey',
        draggable: false,
        left: '8%',
        right: '30%',
        // nodeWidth: 40,
        nodeGap: 10,
        data: nodes,
        label: {
          show: true,
          position: 'right',
          formatter: (params: { name: string; data: typeof nodes[0] }) => {
            const d = params.data
            return `{font|${params.name}}{font2|(${params.data.size})}`;
          },
          rich: {
            grey: {
              color: '#C9CDD4',
              fontSize: 20,
            },
            red: {
              color: '#F53F3F',
              fontSize: 20,
            },
            green: {
              color: '#00B42A',
              fontSize: 20,
            },
            font: {
              color: '#4E5969',
              fontSize: 15,
            },
            font2: {
              color: '#4E5969',
              fontSize: 14,
            }
          },
        },
        links: links,
        lineStyle: {
          color: 'gradient',
          borderColor: 'black',
          borderWidth: 0,
          opacity: 0.3,
          curveness: 0.7,
        },
        emphasis: {
          focus: 'adjacency',
        },
      },
    ],
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove',
      formatter: formatTooltip,
    },
  }

  return option
}

function getEventRole(params: any) {
  if (params.dataType == 'node') {
    const d: ChartNode = params.data
    return d.type == 'interest' ? d.name as AccountInterest : null
  } else {
    const d: ChartLink = params.data
    if (d.source_node?.type == 'interest') {
      return d.source_node.name as AccountInterest
    } else if (d.target_node?.type == 'interest') {
      return d.target_node.name as AccountInterest
    }
    return null
  }
}

function onHover(params: any) {
  const role = getEventRole(params)
  if (role) {
    hoveredINterest.value = role
  } else {
    hoveredINterest.value = null
  }
}

function onLeave() {
  hoveredINterest.value = null
}

function onClick(params: any) {
  const role = getEventRole(params)
  selectedInterest.value = role
  hoveredINterest.value = null
}

watchEffect(() => console.log({selectedInterest: selectedInterest.value}))

</script>

<template>
  <v-chart :option="renderSankeyChart()" autoresize @click="onClick" @mouseover="onHover" @mouseout="onLeave"/>
</template>

<style scoped>
</style>