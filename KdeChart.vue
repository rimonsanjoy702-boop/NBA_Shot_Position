<template>
  <div class="wrap" @click.self="clearAllSelections">
    <!-- KDE主曲线图 -->
    <div ref="kdeChartDom" class="chart-kde" @click.stop="clearAllSelections"></div>

    <!-- 数据统计卡片 -->
    <div class="card-row">
      <div class="stat-card">
        <div class="num">{{ current?.bimodalScore || "--" }}</div>
        <div class="label">双峰指数</div>
      </div>
      <div class="stat-card">
        <div class="num">{{ current?.rimPct || "--" }}%</div>
        <div class="label">篮下出手占比</div>
      </div>
      <div class="stat-card">
        <div class="num">{{ current?.midPct || "--" }}%</div>
        <div class="label">中距离占比</div>
      </div>
      <div class="stat-card">
        <div class="num">{{ current?.threePct || "--" }}%</div>
        <div class="label">三分占比</div>
      </div>
      <div class="stat-card">
        <div class="num">{{ current?.shotCount?.toLocaleString() }}</div>
        <div class="label">赛季总出手</div>
      </div>
    </div>

    <!-- 播放控制区 -->
    <div class="control">
      <button @click="reset">重置</button>
      <button @click="playToggle">{{ play ? "暂停" : "播放" }}</button>
      <input
        v-model.number="index"
        type="range"
        min="0"
        :max="seasonList.length - 1"
        class="slider"
      />
      <span>{{ seasonList[index]?.season }}</span>
      <button v-for="s in [0.5, 1, 2]" :key="s" @click="speed = s">
        {{ s }}x
      </button>
    </div>

    <!-- 双峰指数柱状图 -->
    <div ref="barChartDom" class="chart-bar" @click.stop="clearAllSelections"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import * as echarts from "echarts";
import { useAnalysisContext } from "@/stores/analysisContext";

const store = useAnalysisContext();
function clearAllSelections() { store.clearAll('canvas'); }

// ── F: 桑基L2→KDE联动 — zone距离范围映射 ──
const ZONE_DIST = {
  'RA':  [0, 3], 'Paint': [3, 10], 'MR':   [10, 23],
  'LC3': [22, 24], 'RC3':  [22, 24], 'AB3': [23, 26], 'BC': [26, 40],
}
const ZONE_COLOR = {
  'RA': '#FFE84D', 'Paint': '#FFB800', 'MR': '#FF7A00',
  'LC3': '#FF3300', 'RC3': '#E60000', 'AB3': '#B30005', 'BC': '#800008',
}
const hoverZone = ref(null)  // 当前悬停/选中的 zone key

// 桑基L2点击 → 跳转赛季 + 色带
watch(() => store.selectedZone, (zoneId) => {
  if (!zoneId || !allData.value) { hoverZone.value = null; render(); return }
  const zk = zoneId.replace('L2_', '')
  hoverZone.value = ZONE_DIST[zk] ? zk : null
  // 跳转到当前赛季
  const s = store.selectedSeason
  const idx = seasonList.value.findIndex((x) => x.season === s)
  if (idx >= 0) index.value = idx
  render()
})

const kdeChartDom = ref(null);
const barChartDom = ref(null);
let kdeChart = null;
let barChart = null;

// 数据容器
const allData = ref(null);
const index = ref(0);
const play = ref(false);
const speed = ref(1);
let timer = null;

// 计算属性
const seasonList = computed(() => allData.value?.seasons || []);
const current = computed(() => seasonList.value[index.value]);

// 加载预处理json
async function loadData() {
  const res = await fetch("/data/shot_kde_data.json");
  allData.value = await res.json();
  index.value = seasonList.value.length - 1;
  initEcharts();
}

// 初始化图表
function initEcharts() {
  kdeChart = echarts.init(kdeChartDom.value);
  barChart = echarts.init(barChartDom.value);
  render();
}

// 重绘图表
function render() {
  const list = seasonList.value;
  const curr = list[index.value];
  const first = list[0];
  const last = list.at(-1);

  // KDE曲线配置
  kdeChart.setOption({
    backgroundColor: 'transparent',
    legend: {
      right: 20,
      top: 30,
      textStyle: {
        color: "#e6edf3"
      }
    },
    tooltip: { trigger: "axis", backgroundColor: 'rgba(13,17,23,0.95)', borderColor: 'rgba(255,255,255,0.1)', textStyle: { color: '#e6edf3', fontSize: 13 } },
    title: { text: "NBA投篮距离KDE双峰演化", left: 10, top: 8, textStyle: { color: '#e6edf3' } },
    grid: { left: 44, right: 20, top: 60, bottom: 65 },
    xAxis: {
      type: "value",
      name: "距离 ft",
      nameGap: 14,
      nameTextStyle: { color: '#8b949e' },
      min: 0,
      max: 40,
      axisLabel: { color: '#8b949e' },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
    },
    yAxis: { name: "概率密度", nameTextStyle: { color: '#8b949e' }, axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
    series: [
      {
        name: "1998赛季",
        type: "line",
        data: first.curve.map(i => [i.dist, i.density]),
        lineStyle: { color: "#ff6b6b", width: 2 },
        symbol: "none"
      },
      {
        name: "2020赛季",
        type: "line",
        data: last.curve.map(i => [i.dist, i.density]),
        lineStyle: { color: "#3498db", width: 2 },
        symbol: "none"
      },
      {
        name: curr.season,
        type: "line",
        data: curr.curve.map(i => [i.dist, i.density]),
        lineStyle: { width: 3, color: "#e6edf3" },
        symbol: "none",
        ...(hoverZone.value && ZONE_DIST[hoverZone.value] ? {
          markArea: {
            silent: true,
            data: [[{
              xAxis: ZONE_DIST[hoverZone.value][0],
              itemStyle: { color: ZONE_COLOR[hoverZone.value] || '#fff', opacity: 0.12 }
            }, {
              xAxis: ZONE_DIST[hoverZone.value][1]
            }]]
          }
        } : {})
      }
    ]
  })

  // 双峰柱状图
  barChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { backgroundColor: 'rgba(13,17,23,0.95)', borderColor: 'rgba(255,255,255,0.1)', textStyle: { color: '#e6edf3', fontSize: 13 } },
    title: { text: "历年双峰指数变化", textStyle: { color: '#e6edf3' } },
    xAxis: { data: list.map(s => s.season), axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } } },
    yAxis: { axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
    series: [{
      type: "bar",
      data: list.map((item, i) => ({
        value: item.bimodalScore,
        itemStyle: { color: i === index.value ? "#ffffff" : "#66a8ff" }
      }))
    }]
  })
}

// 播放控制
const playToggle = () => {
  play.value = !play.value;
  if (play.value) {
    timer = setInterval(() => {
      if (index.value >= seasonList.length - 1) {
        play.value = false;
        clearInterval(timer);
        return;
      }
      index.value++;
    }, 500 / speed.value)
  } else {
    clearInterval(timer);
  }
}
const reset = () => {
  clearInterval(timer);
  play.value = false;
  index.value = 0;
}

// 切换赛季重绘 + 同步到 Store
watch(index, (i) => {
  store.setKdeIndex(i, 'kde')
  render()
})
// 播放状态同步到 Store
watch(play, (v) => { v ? store.startAnimation() : store.stopAnimation() })

onMounted(() => loadData())
onUnmounted(() => {
  kdeChart?.dispose();
  barChart?.dispose();
  clearInterval(timer);
})
</script>

<style scoped>
.wrap {
  padding: 20px;
  background: var(--bg-root, #0d1117);
}
.chart-kde {
  width: 100%;
  height: 420px;
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
}
.chart-bar {
  width: 100%;
  height: 260px;
  margin-top: 20px;
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
}
.card-row {
  display: flex;
  gap: 12px;
  margin: 16px 0;
}
.stat-card {
  flex: 1;
  padding: 12px;
  background: var(--bg-card, rgba(255,255,255,0.04));
  text-align: center;
  border-radius: 6px;
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
}
.num {
  font-size: 24px;
  font-weight: bold;
  color: var(--text-primary, #e6edf3);
}
.label {
  font-size: 13px;
  color: var(--text-secondary, #8b949e);
  margin-top: 4px;
}
.control {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px 0;
  color: var(--text-secondary, #8b949e);
}
.control button {
  padding: 3px 10px;
  border-radius: 5px;
  border: 1px solid var(--border-input, rgba(255,255,255,0.12));
  background: var(--bg-input, rgba(255,255,255,0.06));
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  font-size: 12px;
}
.control button:hover {
  background: var(--bg-card-hover, rgba(255,255,255,0.07));
  color: var(--text-primary, #e6edf3);
}
.control span { color: var(--text-primary, #e6edf3); }
.slider {
  flex: 1;
}
</style>
