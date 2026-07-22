<template>
  <div class="three-point-page">
    <!-- ========== 顶部控制栏 ========== -->
    <div class="controls-bar">
      <div class="control-group">
        <span class="control-label">分组切换</span>
        <el-radio-group
          :model-value="store.showMid ? 'all' : 'core'"
          size="small"
          @change="(v: string) => store.toggleMid(v === 'all')"
        >
          <el-radio-button value="core">
            仅先行者 vs 落后者
          </el-radio-button>
          <el-radio-button value="all">
            包含过渡组
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- ========== 加载 / 错误 / 空状态 ========== -->
    <div v-if="store.loading" class="state-box">
      <span class="loading-spinner"></span>
      <span>正在加载三分转型数据…</span>
    </div>
    <div v-else-if="store.error" class="state-box state-error">
      <span>数据加载失败：{{ store.error }}</span>
      <el-button size="small" @click="store.loadAll()">重试</el-button>
    </div>
    <div v-else-if="seasonList.length === 0" class="state-box">
      <span>暂无数据</span>
    </div>

    <!-- ========== 图表画布 ========== -->
    <template v-else>
      <ThreePointCompareChart
        :agg-data="store.aggData"
        :seasons="seasonList"
        :show-mid="store.showMid"
      />

      <!-- ========== 底部图例 + 标注说明 ========== -->
      <div class="legend-bar">
        <div class="legend-items">
          <div class="legend-item">
            <svg width="40" height="12"><line x1="0" y1="6" x2="36" y2="6" stroke="#e63946" stroke-width="3"/></svg>
            <span>先行者 leader ({{ store.leaderTeams.length }} 队)</span>
          </div>
          <div class="legend-item">
            <svg width="40" height="12"><line x1="0" y1="6" x2="36" y2="6" stroke="#457b9d" stroke-width="2" stroke-dasharray="6,3"/></svg>
            <span>落后者 laggard ({{ store.laggardTeams.length }} 队)</span>
          </div>
          <div v-if="store.showMid" class="legend-item">
            <svg width="40" height="12"><line x1="0" y1="6" x2="36" y2="6" stroke="#f4a261" stroke-width="2" stroke-dasharray="2,4"/></svg>
            <span>过渡组 mid ({{ store.midTeams.length }} 队)</span>
          </div>
        </div>
        <div class="annotations">
          <span class="anno-line anno-2015">| 2014-15 先行者窗口终点</span>
          <span class="anno-line anno-2019">| 2018-19 落后者转型起点</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useThreePointCompareStore } from "@/stores/threePointCompare";
import ThreePointCompareChart from "@/components/ThreePointCompareChart.vue";

const store = useThreePointCompareStore();

const seasonList = computed(() => store.seasonList);

onMounted(() => {
  store.loadAll();
});
</script>

<style scoped>
.three-point-page {
  padding: var(--space-lg);
  background: var(--bg-root);
  color: var(--text-primary);
  min-height: 100vh;
}

/* ---- 控制栏 ---- */
.controls-bar {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
}
.control-group {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.control-label {
  font-size: var(--fs-label);
  color: var(--text-secondary);
}

/* ---- 状态 ---- */
.state-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-2xl);
  color: var(--text-secondary);
  font-size: var(--fs-subtitle);
}
.state-error {
  flex-direction: column;
  gap: var(--space-md);
}

/* ---- 图例 ---- */
.legend-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-md);
  margin-top: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  font-size: var(--fs-label);
}
.legend-items {
  display: flex;
  gap: var(--space-lg);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--text-secondary);
}
.annotations {
  display: flex;
  gap: var(--space-lg);
  color: var(--text-tertiary);
  font-size: var(--fs-caption);
}
.anno-2015 { color: #e63946; }
.anno-2019 { color: #457b9d; }
</style>
