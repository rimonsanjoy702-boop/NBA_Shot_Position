<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAnalysisContext } from '@/stores/analysisContext'

const store = useAnalysisContext()
const show = ref(false)
const cardImg = ref('')
const cardTitle = ref('')

// 球员彩蛋配置
const PLAYERS: Record<string, { img: string; title: string }> = {
  'lebron':  { img: '/lebron-card.jpeg', title: '🐐 LeBron James' },
  'howard':  { img: '/howard-card.webp',  title: '🦸 Dwight Howard' },
  'lopez':   { img: '/lopez-card.jpg',    title: '🏔️ Brook Lopez' },
  'harden':  { img: '/harden-card.jpg',   title: '🧔 James Harden' },
  'curry':   { img: '/curry-card.jpg',    title: '👌 Stephen Curry' },
  'leonard': { img: '/leonard-card.webp',  title: '🤖 Kawhi Leonard' },
  'lillard': { img: '/lillard-card.jpg',   title: '⌚ Damian Lillard' },
}

function check(name: string | undefined) {
  if (!name) return
  for (const [key, cfg] of Object.entries(PLAYERS)) {
    if (name.toLowerCase().includes(key)) {
      cardImg.value = cfg.img
      cardTitle.value = cfg.title
      show.value = true
      setTimeout(() => { show.value = false }, 3000)
      return
    }
  }
}

watch(() => store.leftSlot.entityLabel, check)
watch(() => store.rightSlot.entityLabel, check)
</script>

<template>
  <Transition name="card">
    <div v-if="show" class="card-overlay">
      <div class="card-stage">
        <img :src="cardImg" class="card-img" alt="" />
        <div class="card-glare" />
      </div>
      <p class="card-text">{{ cardTitle }}</p>
    </div>
  </Transition>
</template>

<style scoped>
.card-overlay {
  position: fixed; inset: 0; z-index: 10000;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: rgba(13,17,23,0.9);
  pointer-events: none;
}

.card-stage {
  position: relative;
  width: 360px; height: 360px;
  perspective: 800px;
}

.card-img {
  width: 100%; height: 100%;
  object-fit: contain;
  border-radius: 16px;
  border: 3px solid rgba(255,215,0,0.6);
  box-shadow: 0 0 100px rgba(255,215,0,0.3), 0 8px 50px rgba(0,0,0,0.6);
  animation: card-spin 2.8s cubic-bezier(0.22, 0.61, 0.36, 1) both;
}

.card-glare {
  position: absolute; inset: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255,255,255,0) 40%, rgba(255,255,255,0.35) 50%, rgba(255,255,255,0) 60%);
  animation: glare-sweep 2.8s ease-in-out both;
}

.card-text {
  font-size: 32px; font-weight: 900; color: #ffd700;
  margin-top: 24px;
  letter-spacing: 0.06em;
  text-shadow: 0 0 40px rgba(255,215,0,0.5);
  animation: text-pop 2.8s ease-out both;
}

@keyframes card-spin {
  0%   { transform: rotateY(90deg) scale(0.5); opacity: 0; }
  12%  { opacity: 1; }
  28%  { transform: rotateY(0deg) scale(1.03); }
  40%  { transform: rotateY(0deg) scale(1); }
  55%  { transform: rotateY(180deg) scale(1.03); }
  68%  { transform: rotateY(360deg) scale(1); }
  75%  { transform: rotateY(360deg) scale(1); opacity: 1; }
  100% { transform: rotateY(360deg) scale(0.5); opacity: 0; }
}

@keyframes glare-sweep {
  0%   { opacity: 0; }
  30%  { opacity: 0; }
  45%  { opacity: 1; }
  55%  { opacity: 1; }
  60%  { opacity: 0; }
  75%  { opacity: 0; }
  85%  { opacity: 1; }
  95%  { opacity: 1; }
  100% { opacity: 0; }
}

@keyframes text-pop {
  0%   { opacity: 0; transform: translateY(20px); }
  40%  { opacity: 0; transform: translateY(20px); }
  55%  { opacity: 1; transform: translateY(0); }
  75%  { opacity: 1; }
  100% { opacity: 0; transform: translateY(-10px); }
}

.card-enter-active { transition: opacity 0.25s; }
.card-leave-active { transition: opacity 0.5s; }
.card-enter-from,
.card-leave-to { opacity: 0; }
</style>
