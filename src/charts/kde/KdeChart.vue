<template>
  <div class="wrap">
    <!-- KDE主曲线图 -->
    <div ref="kdeChartDom" class="chart-kde"></div>

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
    <div ref="barChartDom" class="chart-bar"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import * as echarts from "echarts";

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
    backgroundColor: "#ffffff",
    title: { text: "NBA投篮距离KDE双峰演化", left: 10 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "value",
      name: "距离 ft",
      min: 0,
      max: 40
    },
    yAxis: { name: "概率密度" },
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
        lineStyle: { width: 3, color: "#222222" },
        symbol: "none"
      }
    ]
  })

  // 双峰柱状图
  barChart.setOption({
    backgroundColor: "#ffffff",
    title: { text: "历年双峰指数变化" },
    xAxis: { data: list.map(s => s.season) },
    yAxis: {},
    series: [{
      type: "bar",
      data: list.map((item, i) => ({
        value: item.bimodalScore,
        itemStyle: { color: i === index.value ? "#ff6b6b" : "#66a8ff" }
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

// 切换赛季重绘
watch(index, () => render())

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
  background: #fff;
}
.chart-kde {
  width: 100%;
  height: 420px;
  border: 1px #eee solid;
}
.chart-bar {
  width: 100%;
  height: 260px;
  margin-top: 20px;
  border: 1px #eee solid;
}
.card-row {
  display: flex;
  gap: 12px;
  margin: 16px 0;
}
.stat-card {
  flex: 1;
  padding: 12px;
  background: #f6f6f6;
  text-align: center;
  border-radius: 6px;
}
.num {
  font-size: 24px;
  font-weight: bold;
  color: #222;
}
.label {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}
.control {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px 0;
}
.slider {
  flex: 1;
}
</style>
