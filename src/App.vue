<script setup lang="ts">
import { RouterView } from 'vue-router';
import { onMounted } from "vue";
import { ElMessage } from "element-plus";
import GlobalNavBar from '@/components/GlobalNavBar.vue';
import PageTransition from '@/components/PageTransition.vue';

async function initApp() {
  console.log('App initialized');
}

onMounted(() => initApp()
    .catch(e => {
      ElMessage.error('Fail to initialize app: ' + e.message);
      throw e;
    }));

</script>

<template>
  <div id="root">
    <GlobalNavBar />
    <PageTransition />
    <div class="app-content">
      <RouterView/>
    </div>
  </div>
</template>

<style>
/* ================================================================
   NBA 投篮可视分析系统 · 共享视觉规范 v1.0 — CSS 变量定义
   来源: NBA可视分析系统_共享视觉规范.md §8
   ================================================================ */

:root {
  /* ===== 背景 ===== */
  --bg-root:        #0d1117;
  --bg-card:        rgba(255,255,255,0.04);
  --bg-card-hover:  rgba(255,255,255,0.07);
  --bg-input:       rgba(255,255,255,0.06);
  --bg-overlay:     rgba(0,0,0,0.75);

  /* ===== 边框 ===== */
  --border-card:    rgba(255,255,255,0.08);
  --border-input:   rgba(255,255,255,0.12);
  --border-hover:   rgba(255,255,255,0.25);
  --border-active:  rgba(52,152,219,0.45);
  --divider:        rgba(255,255,255,0.06);

  /* ===== 文字 ===== */
  --text-primary:   #e6edf3;
  --text-secondary: #8b949e;
  --text-tertiary:  #5c6670;
  --text-inverse:   #0d1117;

  /* ===== 语义色 ===== */
  --semantic-made:      #00d2a0;
  --semantic-missed:    #ff6b6b;
  --semantic-three:     #3498db;
  --semantic-two:       #f39c12;
  --semantic-rim:       #e74c3c;
  --semantic-midrange:  #8b949e;

  /* ===== 功能色 ===== */
  --accent-primary:     #3498db;
  --accent-secondary:   #f39c12;
  --accent-highlight:   #ffffff;
  --chart-grid:         rgba(255,255,255,0.06);
  --chart-axis:         rgba(255,255,255,0.15);

  /* ===== 字体 ===== */
  --font-stack: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                Roboto, 'Helvetica Neue', Arial,
                'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei',
                sans-serif;
  --fs-hero:      32px;
  --fs-title:     20px;
  --fs-subtitle:  14px;
  --fs-body:      13px;
  --fs-label:     12px;
  --fs-caption:   11px;
  --fs-stat:      30px;
  --fs-stat-delta: 11px;

  --lh-heading:   1.2;
  --lh-body:      1.5;
  --lh-compact:   1.1;

  /* ===== 间距 ===== */
  --space-xs:  4px;
  --space-sm:  8px;
  --space-md:  16px;
  --space-lg:  24px;
  --space-xl:  32px;
  --space-2xl: 48px;

  /* ===== 圆角 ===== */
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:   10px;
  --radius-full: 9999px;

  /* ===== 动画 ===== */
  --ease-out:         cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out:      cubic-bezier(0.65, 0, 0.35, 1);
  --duration-fast:    150ms;
  --duration-normal:  400ms;
  --duration-slow:    800ms;
  --duration-play:    500ms;

  /* ===== 阴影 ===== */
  --shadow-card:  0 1px 3px rgba(0,0,0,0.3);
  --shadow-float: 0 4px 12px rgba(0,0,0,0.4);

  /* ===== Hexbin 专用 ===== */
  --court-line:      rgba(255,255,255,0.25);
  --bg-court-floor:  #5a3d1a;

  /* ===== Element Plus 深色覆盖 ===== */
  --el-bg-color: var(--bg-card);
  --el-bg-color-overlay: #1a1e26;
  --el-text-color-primary: var(--text-primary);
  --el-text-color-regular: var(--text-secondary);
  --el-border-color: var(--border-input);
  --el-border-color-hover: var(--border-hover);
  --el-fill-color-blank: var(--bg-input);
  --el-color-primary: var(--accent-primary);
}

html, body, #app {
  padding: 0;
  margin: 0;
  background-color: var(--bg-root);
  color: var(--text-primary);
  font-family: var(--font-stack);
  font-size: var(--fs-body);
  line-height: var(--lh-body);
}

.app-content {
  padding-top: 48px; /* offset for fixed GlobalNavBar */
}
</style>
