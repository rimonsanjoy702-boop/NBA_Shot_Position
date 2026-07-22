<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const active = ref(false)
const showLogo = ref(false)

router.beforeEach(async (to, from, next) => {
  if (from.path === to.path) return next()
  if (active.value) return next()

  // 1) 立刻黑屏遮住旧页面
  active.value = true

  // 等一帧让 DOM 渲染
  await delay(50)

  // 2) Logo 缓缓出现 + 飞过
  showLogo.value = true
  await delay(2200) // 等动画完整播完

  // 3) 跳转新页面（遮罩还在，用户看不到切换）
  next()

  // 4) 等新页面渲染后立即去掉遮罩
  await delay(50)
  showLogo.value = false
  active.value = false
})

function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
</script>

<template>
  <div v-if="active" class="transition-overlay">
    <div class="logo-trail">
      <img
        v-if="showLogo"
        src="/transition-logo.webp"
        class="logo-fly"
        alt="NBA"
      />
    </div>
  </div>
</template>

<style scoped>
.transition-overlay {
  position: fixed; inset: 0; z-index: 9999;
  display: flex; align-items: center; justify-content: center;
  background: #0d1117;
  pointer-events: none;
}

/* ── Logo 飞行：右 → 左 ── */
.logo-trail {
  width: 100%;
  height: 200px;
  overflow: hidden;
}

.logo-fly {
  position: absolute;
  top: 50%;
  width: 240px;
  height: auto;
  transform: translateY(-50%);
  animation: fly-across 2.2s cubic-bezier(0.45, 0, 0.55, 1) both;
}

@keyframes fly-across {
  /* 入场：缓缓出现 (0% → 28%) */
  0%   { right: -280px; opacity: 0; filter: blur(24px); transform: translateY(-50%) scale(0.65); }
  15%  { opacity: 0.35; filter: blur(10px); transform: translateY(-50%) scale(0.88); }
  28%  { opacity: 1;    filter: blur(0);  transform: translateY(-50%) scale(1); }

  /* 中间：短暂停顿 + 微微放大 */
  42%  { right: calc(50% - 120px); opacity: 1; filter: blur(0); transform: translateY(-50%) scale(1.06); }
  50%  { right: calc(50% - 120px); opacity: 1; filter: blur(0); transform: translateY(-50%) scale(1.08); }
  58%  { right: calc(50% - 120px); opacity: 1; filter: blur(0); transform: translateY(-50%) scale(1); }

  /* 出场：缓缓消失 (72% → 100%) */
  85%  { opacity: 0.35; filter: blur(10px); transform: translateY(-50%) scale(0.88); }
  100% { right: calc(100% + 280px); opacity: 0; filter: blur(24px); transform: translateY(-50%) scale(0.65); }
}
</style>
