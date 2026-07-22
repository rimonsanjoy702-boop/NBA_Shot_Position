<template>
  <div class="sankey-page">
    <div class="page-header">
      <h1>NBA Shot Flow 1997-2020</h1>
      <p>Shot Zone → Shot Type → Action Type → Outcome</p>
    </div>

    <div class="filter-header">
      <div class="filter-group">
        <span>图表模式：</span>
        <label>
          <input v-model="areaMode" type="radio" value="7" @change="renderChart">
          完整7分区标准视图
        </label>
      </div>
      <div class="filter-group">
        <button class="play-btn" @click="togglePlay">
          {{ playStatus ? '暂停时序播放' : '自动循环播放赛季' }}
        </button>
      </div>
    </div>

    <div class="season-info">
      <div class="season-title">{{ currentSeason }}</div>
      <div class="season-stats">赛季总出手：{{ totalShot }} | 全场平均命中率：{{ avgFgPct }}</div>
    </div>

    <div class="sankey-wrapper" ref="chartDom"></div>

    <div class="timeline">
      <div class="timeline-header">
        <button class="timeline-btn" @click="prevSeason">上一赛季</button>
        <div class="timeline-years">
          <div
            v-for="s in allSeasonList"
            :key="s"
            class="year-item"
            :class="{ active: currentSeason === s }"
            @click="changeSeason(s)"
          >
            {{ s }}
          </div>
        </div>
        <button class="timeline-btn" @click="nextSeason">下一赛季</button>
      </div>
    </div>

    <div class="info-footer">
      <div class="legend-box">
        <div class="legend-item"><span class="color zone1"></span>禁区</div>
        <div class="legend-item"><span class="color zone2"></span>油漆区</div>
        <div class="legend-item"><span class="color zone3"></span>中距离</div>
        <div class="legend-item"><span class="color zone4"></span>底角三分</div>
        <div class="legend-item"><span class="color zone5"></span>弧顶三分</div>
        <div class="legend-item"><span class="color made"></span>出手命中</div>
        <div class="legend-item"><span class="color missed"></span>出手未中</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { formatFourLayer7ZoneSankey } from '@/util/sankeyDataHandle'

const areaMode = ref('7')
const playStatus = ref(false)
const currentSeason = ref('1997-98')
const totalShot = ref(0)
const avgFgPct = ref('0.000')

const allSeasonList = ref<string[]>([
  '1997-98','1998-99','1999-00','2000-01','2001-02','2002-03','2003-04',
  '2004-05','2005-06','2006-07','2007-08','2008-09','2009-10','2010-11',
  '2011-12','2012-13','2013-14','2014-15','2015-16','2016-17','2017-18',
  '2018-19','2019-20'
])

const chartDom = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
let playTimer: number | null = null
const seasonCache = new Map<string, any>()

const colorMap: Record<string, string> = {
  "Restricted Area (禁区)": "#b82626",
  "In The Paint (Non-RA) (油漆区)": "#ff7733",
  "Mid-Range (中距离)": "#ffb247",
  "Left Corner 3 (左底角三分)": "#82bfff",
  "Right Corner 3 (右底角三分)": "#70b4ff",
  "Above the Break 3 (弧顶三分)": "#4798e8",
  "Backcourt (后场)": "#a0a2a5",
  "2PT Field Goal": "#ff7c43",
  "3PT Field Goal": "#42a8d8",
  "Jump Shot (跳投)": "#73a9ff",
  "Layup / Dunk (上篮/扣篮)": "#ffb866",
  "Step Back (后撤步)": "#c288ff",
  "Catch & Shoot (接球跳投)": "#60d3b6",
  "出手命中": "#28c780",
  "出手未中": "#f76c6c"
}

const changeSeason = (season: string) => {
  currentSeason.value = season
  renderChart()
}
const prevSeason = () => {
  const idx = allSeasonList.value.indexOf(currentSeason.value)
  if (idx > 0) {
    currentSeason.value = allSeasonList.value[idx - 1]
    renderChart()
  }
}
const nextSeason = () => {
  const idx = allSeasonList.value.indexOf(currentSeason.value)
  if (idx < allSeasonList.value.length - 1) {
    currentSeason.value = allSeasonList.value[idx + 1]
    renderChart()
  }
}
const togglePlay = () => {
  playStatus.value = !playStatus.value
  if (playTimer) clearInterval(playTimer)
  if (playStatus.value) {
    playTimer = window.setInterval(() => {
      const idx = allSeasonList.value.indexOf(currentSeason.value)
      currentSeason.value = idx < allSeasonList.value.length - 1 ? allSeasonList.value[idx + 1] : allSeasonList.value[0]
      renderChart()
    }, 1200)
  }
}

const loadSeasonData = async (season: string) => {
  if (seasonCache.has(season)) return seasonCache.get(season)
  const res = await fetch(`/data/sankey_season_${season}.json`)
  const data = await res.json()
  seasonCache.set(season, data)
  return data
}

const renderChart = async () => {
  const json = await loadSeasonData(currentSeason.value)
  const { nodes, links, total, avgPct } = formatFourLayer7ZoneSankey({ data: json })
  totalShot.value = total
  avgFgPct.value = avgPct.toFixed(3)

  if (!chartInstance) return
  const option = {
    backgroundColor: '#ffffff',
    textStyle: { color: '#111111' },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.96)',
      textStyle: { color: '#111' },
      formatter: (params: any) => {
        const data = params.data
        if (data.source && data.target) {
          return `${data.source} → ${data.target}<br/>出手总数：${data.value}`
        }
        return `节点名称：${data.name}`
      }
    },
    series: [
      {
        type: 'sankey',
        left: 40,
        top: 40,
        right: 40,
        bottom: 40,
        nodeWidth: 24,
        nodeGap: 20,
        label: { show: true, color: '#111', fontSize: 14 },
        lineStyle: { curveness: 0.5, color: "source", opacity: 0.65 },
        nodeItemStyle: {
          color: (node: any) => colorMap[node.name] || '#888888',
          borderColor: '#ffffff',
          borderWidth: 1
        },
        data: nodes,
        links: links
      }
    ]
  }
  chartInstance.setOption(option)
}

const initChart = () => {
  if (!chartDom.value) return
  chartInstance = echarts.init(chartDom.value)
}
const resizeHandler = () => chartInstance?.resize()

onMounted(async () => {
  initChart()
  window.addEventListener('resize', resizeHandler)
  await loadSeasonData('1997-98')
  renderChart()
})

onBeforeUnmount(() => {
  if (playTimer) clearInterval(playTimer)
  chartInstance?.dispose()
  chartInstance = null
  window.removeEventListener('resize', resizeHandler)
})
</script>

<style scoped>
.sankey-page {
  width: 100%;
  min-height: 100vh;
  background: #ffffff;
  color: #111;
  padding: 24px;
  box-sizing: border-box;
}
.page-header {
  text-align: center;
  margin-bottom: 24px;
}
.page-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}
.page-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}
.filter-header {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
  align-items: center;
}
.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
}
.filter-group input + label {
  cursor: pointer;
}
.filter-group button {
  background: #e8e8e8;
  color: #111;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
}
.season-info {
  text-align: center;
  margin-bottom: 16px;
}
.season-title {
  font-size: 24px;
  font-weight: bold;
  color: #d49000;
}
.season-stats {
  color: #666;
  margin-top: 4px;
}
.sankey-wrapper {
  width: 100%;
  height: 720px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
}
.timeline {
  margin-top: 20px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}
.timeline-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.timeline-btn {
  background: #e8e8e8;
  color: #111;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
}
.timeline-years {
  flex: 1;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
}
.year-item {
  min-width: 56px;
  text-align: center;
  padding: 8px 12px;
  background: #e8e8e8;
  border-radius: 4px;
  cursor: pointer;
  color: #333;
  font-size: 13px;
  white-space: nowrap;
}
.year-item.active {
  background: #ffd700;
  color: #111;
  font-weight: bold;
}
.info-footer {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
.legend-box {
  display: flex;
  gap: 24px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #333;
  font-size: 14px;
}
.color {
  width: 14px;
  height: 14px;
  border-radius: 3px;
}
.zone1 { background: #b82626; }
.zone2 { background: #ff7733; }
.zone3 { background: #ffb247; }
.zone4 { background: #82bfff; }
.zone5 { background: #4798e8; }
.made { background: #28c780; }
.missed { background: #f76c6c; }
</style>
