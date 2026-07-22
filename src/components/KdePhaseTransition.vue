<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { useAnalysisContext } from '@/stores/analysisContext'
import { nbaColors } from '@/util/colors'

const store = useAnalysisContext()

interface KdePoint { distance: number; density: number }
interface KdeSeason { season: string; year: number; n_shots: number; bimodalityScore: number; rimPct: number; midRangePct: number; threePct: number; curve: KdePoint[] }

const kdeSeasons = ref<KdeSeason[]>([])
const currentIndex = ref(22)
const isPlaying = ref(false)
const speed = ref(1)
let timer: ReturnType<typeof setInterval> | null = null

function loadKdeData() {
  fetch('/demo-data/distance_kde.json')
    .then(r => r.json())
    .then(data => { kdeSeasons.value = data.kdeData || []; currentIndex.value = Math.min(currentIndex.value, kdeSeasons.value.length-1) })
    .catch(() => { generateMockKde() })
}
function generateMockKde() {
  const seasons: KdeSeason[] = []
  for (let y = 1998; y <= 2020; y++) {
    const t = (y-1998)/22
    const curve: KdePoint[] = []
    for (let d = 0; d <= 40; d += 0.25) {
      const rimPeak = (0.04 + t*0.02) * Math.exp(-(((d-1.5)/(1.5+t*0.3))**2))
      const threePeak = (0.015 + t*0.025) * Math.exp(-(((d-23.5)/(2.5-t*0.3))**2))
      const mid = 0.02 * (1-t*0.5) * Math.exp(-(((d-14)/4)**2))
      curve.push({ distance: d, density: +(rimPeak+threePeak+mid+0.002).toFixed(6) })
    }
    seasons.push({ season: `${y-1}-${String(y).slice(-2)}`, year: y, n_shots: 180000+Math.floor(Math.random()*30000), bimodalityScore: +(4.5+t*3.5).toFixed(1), rimPct: +(30+t*4).toFixed(1), midRangePct: +(28-t*14).toFixed(1), threePct: +(14+t*11).toFixed(1), curve })
  }
  kdeSeasons.value = seasons
}
onMounted(() => { loadKdeData(); window.addEventListener('keydown', onKey) })
onUnmounted(() => { if(timer) clearInterval(timer); window.removeEventListener('keydown', onKey) })

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') { currentIndex.value = Math.max(0, currentIndex.value-1); store.setKdeIndex(currentIndex.value, 'kde') }
  if (e.key === 'ArrowRight') { currentIndex.value = Math.min(kdeSeasons.value.length-1, currentIndex.value+1); store.setKdeIndex(currentIndex.value, 'kde') }
  if (e.key === ' ') { e.preventDefault(); togglePlay() }
}

function togglePlay() {
  if (isPlaying.value) { stopPlay() }
  else { startPlay() }
}
function startPlay() {
  isPlaying.value = true; store.startAnimation()
  timer = setInterval(() => {
    if (currentIndex.value >= kdeSeasons.value.length-1) { stopPlay(); return }
    currentIndex.value++
    store.setKdeIndex(currentIndex.value, 'kde')
    store.setSeason(kdeSeasons.value[currentIndex.value]?.season || store.selectedSeason, 'kde')
  }, Math.round(500/speed.value))
}
function stopPlay() { isPlaying.value = false; store.stopAnimation(); if(timer) { clearInterval(timer); timer = null } }

watch(currentIndex, (i) => {
  if (kdeSeasons.value[i]) store.setSeason(kdeSeasons.value[i].season, 'kde')
})

const cur = computed(() => kdeSeasons.value[currentIndex.value])
const first = computed(() => kdeSeasons.value[0])
const last = computed(() => kdeSeasons.value[kdeSeasons.value.length-1])

const kdeOption = computed(() => {
  if (!cur.value) return {}
  const dists = cur.value.curve.map(p => p.distance)
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' as const, backgroundColor: 'rgba(13,17,23,0.95)', borderColor: 'rgba(255,255,255,0.1)', textStyle: { color: '#e6edf3', fontSize: 13 } },
    legend: { data: ['1997-98(早期)','2019-20(近期)',`${cur.value.season}(当前)`], bottom: 6, textStyle: { color: '#8b949e', fontSize: 11 } },
    grid: { left: 44, right: 44, top: 16, bottom: 32 },
    xAxis: { type: 'category' as const, data: dists, name: '投篮距离(ft)', nameTextStyle: { color: '#8b949e', fontSize: 11 }, axisLabel: { color: '#8b949e', fontSize: 10, interval: 19 }, axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } } },
    yAxis: { type: 'value' as const, axisLabel: { color: '#8b949e', fontSize: 10, formatter: (v:number)=>(v*1000).toFixed(0) }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
    series: [
      { name: '1997-98(早期)', type: 'line', data: first.value?.curve.map(p=>p.density)||[], smooth: true, symbol: 'none', lineStyle: { color: nbaColors.earlySeason, width: 1.5, opacity: 0.5 }, animation: false },
      { name: '2019-20(近期)', type: 'line', data: last.value?.curve.map(p=>p.density)||[], smooth: true, symbol: 'none', lineStyle: { color: nbaColors.lateSeason, width: 1.5, opacity: 0.5 }, animation: false },
      { name: `${cur.value.season}(当前)`, type: 'line', data: cur.value.curve.map(p=>p.density), smooth: true, symbol: 'none', lineStyle: { color: '#fff', width: 3 }, areaStyle: { color: { type:'linear',x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:'rgba(52,152,219,0.2)'},{offset:1,color:'rgba(52,152,219,0.02)'}] } }, animation: true, animationDuration: 400 },
    ],
  }
})

const bimOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'axis' as const, backgroundColor: 'rgba(13,17,23,0.95)', borderColor: 'rgba(255,255,255,0.1)', textStyle: { color: '#e6edf3', fontSize: 13 } },
  grid: { left: 40, right: 16, top: 10, bottom: 24 },
  xAxis: { type: 'category' as const, data: kdeSeasons.value.map(s=>s.year), axisLabel: { color: '#8b949e', fontSize: 10, interval: 3 } },
  yAxis: { type: 'value' as const, name: '双峰指数', nameTextStyle: { color: '#8b949e', fontSize: 11 }, axisLabel: { color: '#8b949e', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
  series: [{ type: 'bar', data: kdeSeasons.value.map((s,i)=>({ value: s.bimodalityScore, itemStyle: { color: i===currentIndex.value ? nbaColors.bimodalityActive : s.bimodalityScore>6.5 ? nbaColors.bimodalityHigh : nbaColors.bimodalityLow, borderRadius: [2,2,0,0] } })), animation: true, animationDuration: 300 }],
}))
</script>

<template>
  <div class="kde-container">
    <div class="kde-header">
      <span class="kde-title">📊 投篮距离分布演化 — 从单峰到双峰</span>
      <span class="kde-badge">{{ cur?.season }}</span>
    </div>
    <v-chart :option="kdeOption" autoresize style="width:100%;height:320px" />
    <div class="kde-controls">
      <button class="ctrl-btn" @click="togglePlay">{{ isPlaying ? '⏸️' : '▶️' }}</button>
      <button class="ctrl-btn" @click="currentIndex=0;store.setKdeIndex(0,'kde')">⏮️</button>
      <input type="range" min="0" :max="kdeSeasons.length-1" v-model="currentIndex" class="kde-slider" />
      <span class="speed-label">速度</span>
      <button v-for="s in [0.5,1,2]" :key="s" :class="['speed-btn',{active:speed===s}]" @click="speed=s">{{ s }}×</button>
    </div>
    <div class="kde-stats" v-if="cur">
      <div class="stat"><span class="stat-val">{{ cur.bimodalityScore }}</span><span class="stat-lbl">双峰指数</span></div>
      <div class="stat"><span class="stat-val rim">{{ cur.rimPct }}%</span><span class="stat-lbl">🏀篮下</span></div>
      <div class="stat"><span class="stat-val mid">{{ cur.midRangePct }}%</span><span class="stat-lbl">📉中距离</span></div>
      <div class="stat"><span class="stat-val three">{{ cur.threePct }}%</span><span class="stat-lbl">🎯三分</span></div>
      <div class="stat"><span class="stat-val">{{ ((cur.n_shots)/1000).toFixed(0) }}K</span><span class="stat-lbl">出手数</span></div>
    </div>
    <div class="bimodality-section">
      <div class="bim-header"><span>📈 双峰指数趋势</span><span class="bim-hint">指数越高=双峰越明显</span></div>
      <v-chart :option="bimOption" autoresize style="width:100%;height:180px" />
    </div>
    <div class="kde-hint">💡 ← → 逐帧 · 空格 播放/暂停</div>
  </div>
</template>

<style scoped>
.kde-container { background: var(--bg-card); border: 1px solid var(--border-card); border-radius: 10px; padding: 14px 16px 8px; }
.kde-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.kde-title { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.kde-badge { background: rgba(52,152,219,0.15); color: var(--accent-primary); font-size: 12px; font-weight: 700; padding: 2px 10px; border-radius: 10px; }
.kde-controls { display: flex; align-items: center; gap: 8px; padding: 8px 0; }
.ctrl-btn { width: 32px; height: 32px; border-radius: 6px; border: 1px solid var(--border-input); background: rgba(255,255,255,0.05); color: var(--text-primary); font-size: 14px; cursor: pointer; }
.ctrl-btn:hover { background: var(--bg-card-hover); }
.kde-slider { flex: 1; -webkit-appearance: none; height: 5px; border-radius: 3px; background: rgba(255,255,255,0.1); cursor: pointer; }
.kde-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%; background: var(--accent-primary); cursor: pointer; }
.speed-btn { padding: 3px 10px; border-radius: 5px; border: 1px solid var(--border-input); background: transparent; color: var(--text-secondary); font-size: 11px; cursor: pointer; }
.speed-btn.active { background: rgba(52,152,219,0.2); border-color: var(--border-active); color: var(--accent-primary); }
.speed-label { font-size: 11px; color: var(--text-secondary); }
.kde-stats { display: flex; gap: 8px; margin: 4px 0 8px; }
.stat { flex: 1; text-align: center; background: rgba(255,255,255,0.03); border-radius: 6px; padding: 6px 4px; }
.stat-val { display: block; font-size: 20px; font-weight: 800; color: var(--text-primary); line-height: 1.1; }
.stat-val.rim { color: #ff6b6b; } .stat-val.mid { color: #8b949e; } .stat-val.three { color: #3498db; }
.stat-lbl { font-size: 10px; color: var(--text-secondary); }
.bimodality-section { margin-top: 4px; }
.bim-header { display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 2px; }
.bim-hint { font-size: 10px; color: var(--text-tertiary); }
.kde-hint { text-align: center; color: var(--text-tertiary); font-size: 10px; padding: 4px 0 0; }
</style>
