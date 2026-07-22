<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAnalysisContext } from '@/stores/analysisContext'

const router = useRouter()
const route = useRoute()
const store = useAnalysisContext()

const tabs = [
  { path: '/space',     label: '空间探索', icon: '🏀' },
  { path: '/evolution', label: '演化趋势', icon: '📈' },
  { path: '/structure', label: '投篮结构', icon: '🔀' },
]

function go(path: string) {
  router.push(path)
}

function clearEntity() {
  store.clearEntity('navbar')
}
</script>

<template>
  <nav class="global-nav">
    <div class="nav-left">
      <span class="nav-brand" @click="go('/space')">🏀 NBA Shot Evolution</span>
      <div class="nav-tabs">
        <button
          v-for="tab in tabs" :key="tab.path"
          :class="['nav-tab', { active: route.path === tab.path }]"
          @click="go(tab.path)"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>
    </div>
    <div class="nav-right">
      <span class="nav-season">📅 {{ store.selectedSeason }}</span>
      <span class="nav-entity" :class="store.entityLabel.type">
        {{ store.entityLabel.type === 'player' ? '👤' : store.entityLabel.type === 'team' ? '🏠' : '🌐' }}
        {{ store.entityLabel.text }}
        <button
          v-if="store.entityLabel.type !== 'league'"
          class="clear-btn"
          @click="clearEntity"
          title="清除选择"
        >×</button>
      </span>
    </div>
  </nav>
</template>

<style scoped>
.global-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(13,17,23,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-card);
}
.nav-left { display: flex; align-items: center; gap: 20px; }
.nav-brand {
  font-size: 17px; font-weight: 800; color: var(--text-primary);
  cursor: pointer; letter-spacing: 0.02em; user-select: none;
}
.nav-tabs { display: flex; gap: 4px; }
.nav-tab {
  padding: 7px 18px; border-radius: 8px; border: none;
  background: transparent; color: var(--text-secondary);
  font-size: 13px; font-weight: 600; cursor: pointer;
  transition: all 0.15s; display: flex; align-items: center; gap: 6px;
}
.nav-tab:hover { background: var(--bg-card-hover); color: var(--text-primary); }
.nav-tab.active {
  background: rgba(52,152,219,0.15); color: var(--accent-primary);
}
.tab-icon { font-size: 16px; }

.nav-right { display: flex; align-items: center; gap: 14px; }
.nav-season {
  font-size: 13px; font-weight: 700; color: var(--accent-primary);
  background: rgba(52,152,219,0.1); padding: 4px 12px; border-radius: 6px;
}
.nav-entity {
  font-size: 13px; color: var(--text-secondary);
  display: flex; align-items: center; gap: 6px;
}
.nav-entity.player { color: var(--accent-primary); }
.nav-entity.team { color: var(--semantic-made); }
.clear-btn {
  width: 20px; height: 20px; border-radius: 50%;
  border: 1px solid var(--border-input); background: transparent;
  color: var(--text-secondary); cursor: pointer;
  font-size: 12px; display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.clear-btn:hover { background: rgba(255,107,107,0.2); border-color: var(--semantic-missed); color: var(--semantic-missed); }
</style>
