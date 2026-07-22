<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import VChart from 'vue-echarts'
import { useAnalysisContext } from '@/stores/analysisContext'
import { nbaColors } from '@/util/colors'

const store = useAnalysisContext()

// ── Mock sankey data ──
const sankeyOption = computed(() => {
  const nodes = [
    { name: '禁区', itemStyle: { color: nbaColors.rim } },
    { name: '油漆区', itemStyle: { color: '#e67e22' } },
    { name: '中距离', itemStyle: { color: nbaColors.midRange } },
    { name: '左底角三分', itemStyle: { color: nbaColors.threePT } },
    { name: '右底角三分', itemStyle: { color: nbaColors.threePT } },
    { name: '弧顶三分', itemStyle: { color: nbaColors.threePTLine } },
    { name: '后场', itemStyle: { color: '#666' } },
    { name: '2PT', itemStyle: { color: nbaColors.twoPT } },
    { name: '3PT', itemStyle: { color: nbaColors.threePTLine } },
    { name: '跳投', itemStyle: { color: '#9b59b6' } },
    { name: '上篮/扣篮', itemStyle: { color: '#e74c3c' } },
    { name: '后撤步', itemStyle: { color: '#f39c12' } },
    { name: '命中', itemStyle: { color: nbaColors.made } },
    { name: '未中', itemStyle: { color: nbaColors.missed } },
  ]
  const links = [
    { source:'禁区', target:'2PT', value:3800 }, { source:'油漆区', target:'2PT', value:2900 },
    { source:'中距离', target:'2PT', value:2200 }, { source:'左底角三分', target:'3PT', value:900 },
    { source:'右底角三分', target:'3PT', value:950 }, { source:'弧顶三分', target:'3PT', value:3400 },
    { source:'后场', target:'3PT', value:80 },
    { source:'2PT', target:'上篮/扣篮', value:4200 }, { source:'2PT', target:'跳投', value:3400 }, { source:'2PT', target:'后撤步', value:600 },
    { source:'3PT', target:'跳投', value:4800 }, { source:'3PT', target:'后撤步', value:350 },
    { source:'上篮/扣篮', target:'命中', value:2700 }, { source:'上篮/扣篮', target:'未中', value:1500 },
    { source:'跳投', target:'命中', value:3800 }, { source:'跳投', target:'未中', value:4400 },
    { source:'后撤步', target:'命中', value:420 }, { source:'后撤步', target:'未中', value:530 },
  ]

  const zoneNames = ['禁区','油漆区','中距离','左底角三分','右底角三分','弧顶三分','后场']
  if (store.selectedZone && zoneNames.includes(store.selectedZone)) {
    const hitLinks = new Set<string>()
    links.forEach(l => {
      if (l.source === store.selectedZone) hitLinks.add(`${l.source}→${l.target}`)
    })
    links.forEach(l => {
      const key = `${l.source}→${l.target}`
      if (!hitLinks.has(key)) l.value = Math.floor(l.value * 0.03)
    })
  }

  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item' as const, triggerOn: 'mousemove' as const, backgroundColor: 'rgba(13,17,23,0.95)', borderColor: 'rgba(255,255,255,0.1)', textStyle: { color: '#e6edf3', fontSize: 13 }, formatter: (p:any) => p.dataType==='node' ? `${p.name}` : `${p.data.source} → ${p.data.target}: ${p.data.value}次` },
    series: [{
      type: 'sankey' as const, left: '4%', right: '18%', nodeWidth: 18, nodeGap: 8,
      data: nodes, links, layoutIterations: 0,
      label: { show: true, position: 'right' as const, color: '#8b949e', fontSize: 11 },
      lineStyle: { color: 'gradient', curveness: 0.5, opacity: 0.2 },
      emphasis: { focus: 'adjacency' as const },
    }],
  }
})

function onClick(params: any) {
  if (params.dataType === 'node') {
    const name = params.data?.name
    const zones = ['禁区','油漆区','中距离','左底角三分','右底角三分','弧顶三分','后场']
    const types = ['2PT','3PT']
    const outcomes = ['命中','未中']
    if (zones.includes(name)) {
      store.setZone(store.selectedZone===name?null:name, 'sankey')
    } else if (types.includes(name)) {
      store.setShotType(store.selectedShotType===name?null:(name as '2PT'|'3PT'), 'sankey')
    } else if (outcomes.includes(name)) {
      // color highlight only
    }
  }
}
</script>

<template>
  <div class="sankey-container">
    <div class="sankey-header">
      <span class="sankey-title">🔀 投篮选择流向</span>
      <span class="sankey-meta">{{ store.selectedSeason }} · {{ store.entityLabel.text }}</span>
    </div>
    <v-chart :option="sankeyOption" autoresize style="width:100%;height:380px" @click="onClick" />
    <div class="sankey-footer">
      <div class="flow-legend">
        <span class="flow-label">列: </span>
        <span class="flow-tag zone">投篮区域</span><span>→</span>
        <span class="flow-tag type">投篮类型</span><span>→</span>
        <span class="flow-tag action">投篮动作</span><span>→</span>
        <span class="flow-tag result">结果</span>
      </div>
      <div class="sankey-hint">💡 点击节点 → 联动 Hexbin | 再点取消</div>
    </div>
  </div>
</template>

<style scoped>
.sankey-container { background: var(--bg-card); border: 1px solid var(--border-card); border-radius: 10px; padding: 14px 16px 8px; }
.sankey-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.sankey-title { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.sankey-meta { font-size: 12px; color: var(--text-secondary); }
.sankey-footer { display: flex; justify-content: space-between; align-items: center; padding: 4px 0 0; }
.flow-legend { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-secondary); }
.flow-tag { padding: 1px 8px; border-radius: 4px; font-size: 10px; }
.flow-tag.zone { background: rgba(255,107,107,0.1); color: #ff6b6b; }
.flow-tag.type { background: rgba(243,156,18,0.1); color: #f39c12; }
.flow-tag.action { background: rgba(155,89,182,0.1); color: #9b59b6; }
.flow-tag.result { background: rgba(0,210,160,0.1); color: #00d2a0; }
.sankey-hint { font-size: 10px; color: var(--text-tertiary); text-align: right; }
</style>
