<script setup lang="ts">
import { accountInterests } from "@/models.ts";
import { interestColorMap } from "@/util/colors.ts";

const selectedInterest = defineModel<string | null>('selectedInterest', {required: true});

const NODE_SIZE = 1000
const EDGE_SIZE = 100

const nodes = Object.fromEntries(Array.from({length: NODE_SIZE}, (_, i) => [`node-${i}`, {
  id: `node-${i}`,
  x: Math.random() * 800,
  y: Math.random() * 400,
  size: Math.random() * 10,
  interest: accountInterests[Math.floor(Math.random() * accountInterests.length)],
}]));

const edges = Array.from({length: EDGE_SIZE}, (_, i) => ({
  source: `node-${Math.floor(Math.random() * NODE_SIZE)}`,
  target: `node-${Math.floor(Math.random() * NODE_SIZE)}`,
  weight: Math.random() * 5,
}))

function onNodeClick(node: typeof nodes[number]) {
  selectedInterest.value = node.interest;
}


</script>

<template>
  <svg viewBox="0 0 800 400" style="display: block">
    <g id="edges">
      <line v-for="(edge, index) in edges" :key="index"
            :x1="nodes[edge.source].x" :y1="nodes[edge.source].y"
            :x2="nodes[edge.target].x" :y2="nodes[edge.target].y"
            stroke="#ddd" :stroke-width="edge.weight"/>
    </g>


    <g id="nodes">
      <circle v-for="(node, index) in nodes" :key="index"
              :cx="node.x" :cy="node.y" :r="node.size"
              :fill="interestColorMap[node.interest] + (node.interest === selectedInterest ? 'FF' : '33')"
              style="cursor: pointer"
              @click="onNodeClick(node)"/>
    </g>

  </svg>
</template>