<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const sections = [
  { path: '/dashboard', label: '进入仪表盘', desc: '投篮热力图 · 衰减曲线 · 距离演化 · 三分转型 · 桑基图', icon: '📊' },
]

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="home">
    <!-- 背景图层 -->
    <div class="home-bg" />
    <div class="home-overlay" />

    <!-- 内容 -->
    <div class="home-content">
      <div class="home-hero">
        <h1 class="home-title">🏀 NBA Shot Evolution</h1>
        <p class="home-subtitle">1997–2020 赛季 · 470 万次投篮 · 可视分析系统</p>
      </div>

      <div class="home-cards">
        <div
          v-for="s in sections"
          :key="s.path"
          class="home-card"
          @click="go(s.path)"
        >
          <span class="card-icon">{{ s.icon }}</span>
          <div class="card-body">
            <span class="card-label">{{ s.label }}</span>
            <span class="card-desc">{{ s.desc }}</span>
          </div>
          <span class="card-arrow">→</span>
        </div>
      </div>

      <p class="home-hint">点击卡片进入对应分析视图</p>
    </div>
  </div>
</template>

<style scoped>
.home {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* ── 背景图片 ── */
.home-bg {
  position: absolute;
  inset: 0;
  background: url('/bg-home.jpeg') center / cover no-repeat;
  transform: scale(1.05);
  filter: blur(2px) brightness(0.35);
  z-index: 0;
}

/* ── 渐变叠加 ── */
.home-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 50% 30%, rgba(52,152,219,0.15) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 70%, rgba(243,156,18,0.1) 0%, transparent 50%),
    linear-gradient(180deg, rgba(13,17,23,0.3) 0%, rgba(13,17,23,0.85) 100%);
  z-index: 1;
}

/* ── 内容 ── */
.home-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  padding: 40px 24px;
}

.home-hero {
  text-align: center;
}

.home-title {
  font-size: 48px;
  font-weight: 900;
  color: #fff;
  margin: 0;
  letter-spacing: 0.03em;
  text-shadow: 0 4px 24px rgba(0,0,0,0.5);
}

.home-subtitle {
  font-size: 16px;
  color: rgba(255,255,255,0.6);
  margin: 12px 0 0;
  font-weight: 400;
  letter-spacing: 0.05em;
}

/* ── 卡片 ── */
.home-cards {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

.home-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 24px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  backdrop-filter: blur(8px);
  min-width: 280px;
}

.home-card:hover {
  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.25);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.card-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.card-label {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.card-desc {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
}

.card-arrow {
  font-size: 18px;
  color: rgba(255,255,255,0.3);
  flex-shrink: 0;
  transition: all 0.25s ease;
}

.home-card:hover .card-arrow {
  color: #3498db;
  transform: translateX(4px);
}

/* ── 底部提示 ── */
.home-hint {
  font-size: 12px;
  color: rgba(255,255,255,0.3);
  margin: 0;
}
</style>
