<script setup lang="ts">
/**
 * HexbinControls.vue — Selector bar above the court.
 * Props: seasons[], teams[], players[], half-court selection (2-way bind)
 */
import { computed } from 'vue';
import type { HalfCourtSelection } from '../types';
import { ALL_SEASONS } from '../types';

const props = defineProps<{
  /** Available teams in this season's data */
  teams: { id: number; name: string; abbr: string }[];
  /** Available players in this season's data */
  players: { id: number; name: string }[];
  /** Left half-court selection */
  leftSelection: HalfCourtSelection;
  /** Right half-court selection */
  rightSelection: HalfCourtSelection;
}>();

const emit = defineEmits<{
  'update:leftSelection': [v: HalfCourtSelection];
  'update:rightSelection': [v: HalfCourtSelection];
}>();

// Scope options
const scopeOptions = [
  { value: 'league' as const, label: '联盟' },
  { value: 'team' as const, label: '球队' },
  { value: 'player' as const, label: '球员' },
];

// Current scope for each side
const leftScope = computed(() => props.leftSelection.scope);
const rightScope = computed(() => props.rightSelection.scope);

// Available entities based on scope
const leftEntities = computed(() =>
  leftScope.value === 'team' ? props.teams : props.players
);
const rightEntities = computed(() =>
  rightScope.value === 'team' ? props.teams : props.players
);

// Selected entity id
const leftEntityId = computed(() => props.leftSelection.entityId ?? null);
const rightEntityId = computed(() => props.rightSelection.entityId ?? null);

function onLeftScopeChange(scope: 'league' | 'team' | 'player') {
  emit('update:leftSelection', { ...props.leftSelection, scope, entityId: undefined });
}
function onRightScopeChange(scope: 'league' | 'team' | 'player') {
  emit('update:rightSelection', { ...props.rightSelection, scope, entityId: undefined });
}
function onLeftEntityChange(entityId: number) {
  const entity = leftEntities.value.find((e) => e.id === entityId);
  emit('update:leftSelection', { ...props.leftSelection, entityId, entityLabel: entity?.name });
}
function onRightEntityChange(entityId: number) {
  const entity = rightEntities.value.find((e) => e.id === entityId);
  emit('update:rightSelection', { ...props.rightSelection, entityId, entityLabel: entity?.name });
}
function onLeftSeasonChange(season: string) {
  emit('update:leftSelection', { ...props.leftSelection, season });
}
function onRightSeasonChange(season: string) {
  emit('update:rightSelection', { ...props.rightSelection, season });
}
</script>

<template>
  <div class="hexbin-controls">
    <!-- Left half-court controls -->
    <div class="control-group">
      <span class="half-label">左半场</span>

      <el-select
        :model-value="leftScope"
        @update:model-value="onLeftScopeChange"
        size="small"
        style="width: 80px"
      >
        <el-option
          v-for="opt in scopeOptions"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>

      <el-select
        v-if="leftScope !== 'league'"
        :model-value="leftEntityId"
        @update:model-value="onLeftEntityChange"
        size="small"
        style="width: 140px"
        filterable
        placeholder="选择..."
      >
        <el-option
          v-for="e in leftEntities"
          :key="e.id"
          :label="e.name"
          :value="e.id"
        />
      </el-select>

      <el-select
        :model-value="leftSelection.season"
        @update:model-value="onLeftSeasonChange"
        size="small"
        style="width: 110px"
      >
        <el-option
          v-for="s in ALL_SEASONS"
          :key="s"
          :label="s"
          :value="s"
        />
      </el-select>
    </div>

    <!-- Center shared controls -->
    <div class="control-group center-group">
      <span class="half-label">中场</span>
      <!-- Placeholder: fixed scale toggle, play button -->
      <el-button size="small" disabled>固定标尺</el-button>
      <el-button size="small" disabled>▶ 播放</el-button>
    </div>

    <!-- Right half-court controls -->
    <div class="control-group">
      <span class="half-label">右半场</span>

      <el-select
        :model-value="rightScope"
        @update:model-value="onRightScopeChange"
        size="small"
        style="width: 80px"
      >
        <el-option
          v-for="opt in scopeOptions"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>

      <el-select
        v-if="rightScope !== 'league'"
        :model-value="rightEntityId"
        @update:model-value="onRightEntityChange"
        size="small"
        style="width: 140px"
        filterable
        placeholder="选择..."
      >
        <el-option
          v-for="e in rightEntities"
          :key="e.id"
          :label="e.name"
          :value="e.id"
        />
      </el-select>

      <el-select
        :model-value="rightSelection.season"
        @update:model-value="onRightSeasonChange"
        size="small"
        style="width: 110px"
      >
        <el-option
          v-for="s in ALL_SEASONS"
          :key="s"
          :label="s"
          :value="s"
        />
      </el-select>
    </div>
  </div>
</template>

<style scoped>
.hexbin-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md, 16px);
  padding: var(--space-sm, 8px) var(--space-md, 16px);
  background: var(--bg-card, rgba(255,255,255,0.04));
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  border-radius: var(--radius-md, 8px);
}

.control-group {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 8px);
}

.center-group {
  flex-shrink: 0;
}

.half-label {
  font-size: var(--fs-caption, 11px);
  font-weight: 600;
  color: var(--text-secondary, #8b949e);
  text-transform: uppercase;
  white-space: nowrap;
}
</style>
