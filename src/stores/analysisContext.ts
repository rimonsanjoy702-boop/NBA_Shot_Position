import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// ═══════════════════════════════════════════════════════════
// Data slot — one independent data context (season + entity)
// ═══════════════════════════════════════════════════════════

export interface DataSlot {
  season: string                          // "2019-20"
  scope: 'league' | 'team' | 'player'
  entityId?: number
  entityLabel?: string
}

export const useAnalysisContext = defineStore('analysisContext', () => {
  // ═══ 左右数据槽（黄金三角共享） ═══
  const leftSlot = ref<DataSlot>({ season: '2019-20', scope: 'league' })
  const rightSlot = ref<DataSlot>({ season: '2019-20', scope: 'league' })

  /** Which side receives time-bin click effects from decay-curve / sankey L1 */
  const activeSide = ref<'left' | 'right'>('left')

  // ═══ 时间 Bin 选中 ═══
  /** null = 全时段, 0-7 = 具体时段 (Q1前~Q4后) */
  const selectedTimeBin = ref<number | null>(null)

  // ═══ 桑基图选中状态 ═══
  const selectedZone = ref<string | null>(null)       // L2 区域 id, e.g. "L2_AB3"
  const selectedAction = ref<string | null>(null)     // L3 出手方式 id, e.g. "L3_Jump"
  const selectedOutcome = ref<string | null>(null)    // L4 结果 id, e.g. "L4_Made"

  // ═══ KDE 动画状态 ═══
  const isKdeAnimating = ref(false)
  const kdeCurrentIndex = ref(22)  // default: last season
  const playSpeed = ref(1)

  // ═══ 联动追踪 ═══
  const lastChangeSource = ref<string>('init')

  // ═══════════════════════════════════════════════════════════
  // Derived — convenience accessors for legacy consumers
  // ═══════════════════════════════════════════════════════════

  /** Slot for the currently active side */
  const activeSlot = computed(() =>
    activeSide.value === 'left' ? leftSlot.value : rightSlot.value
  )

  /** Current season from active slot (used by GlobalNavBar) */
  const selectedSeason = computed(() => activeSlot.value.season)

  /** Entity label from active slot (used by GlobalNavBar) */
  const entityLabel = computed(() => {
    const slot = activeSlot.value
    if (slot.entityLabel) {
      return {
        text: slot.entityLabel,
        type: slot.scope === 'player' ? 'player' as const : 'team' as const,
      }
    }
    return { text: '联盟平均', type: 'league' as const }
  })

  // ═══════════════════════════════════════════════════════════
  // Actions — Slot management
  // ═══════════════════════════════════════════════════════════

  function setSlot(side: 'left' | 'right', patch: Partial<DataSlot>, source: string) {
    lastChangeSource.value = source
    if (side === 'left') {
      leftSlot.value = { ...leftSlot.value, ...patch }
    } else {
      rightSlot.value = { ...rightSlot.value, ...patch }
    }
  }

  function setActiveSide(side: 'left' | 'right', source: string) {
    lastChangeSource.value = source
    activeSide.value = side
  }

  // ═══════════════════════════════════════════════════════════
  // Actions — Time bin
  // ═══════════════════════════════════════════════════════════

  function setTimeBin(bin: number | null, source: string) {
    lastChangeSource.value = source
    selectedTimeBin.value = selectedTimeBin.value === bin ? null : bin
  }

  function clearTimeBin(source: string) {
    lastChangeSource.value = source
    selectedTimeBin.value = null
  }

  // ═══════════════════════════════════════════════════════════
  // Actions — Sankey selections
  // ═══════════════════════════════════════════════════════════

  function setZone(zone: string | null, source: string) {
    lastChangeSource.value = source
    selectedZone.value = selectedZone.value === zone ? null : zone
  }

  function setAction(action: string | null, source: string) {
    lastChangeSource.value = source
    selectedAction.value = selectedAction.value === action ? null : action
  }

  function setOutcome(outcome: string | null, source: string) {
    lastChangeSource.value = source
    selectedOutcome.value = selectedOutcome.value === outcome ? null : outcome
  }

  function clearSankeySelections(source: string) {
    lastChangeSource.value = source
    selectedZone.value = null
    selectedAction.value = null
    selectedOutcome.value = null
  }

  // ═══════════════════════════════════════════════════════════
  // Actions — All clear
  // ═══════════════════════════════════════════════════════════

  function clearAll(source: string) {
    lastChangeSource.value = source
    selectedTimeBin.value = null
    selectedZone.value = null
    selectedAction.value = null
    selectedOutcome.value = null
  }

  // ═══════════════════════════════════════════════════════════
  // Actions — KDE
  // ═══════════════════════════════════════════════════════════

  function setKdeIndex(index: number, source: string) {
    lastChangeSource.value = source
    kdeCurrentIndex.value = index
  }

  function startAnimation() { isKdeAnimating.value = true }
  function stopAnimation() { isKdeAnimating.value = false }

  return {
    // Slots
    leftSlot, rightSlot, activeSide, activeSlot,
    // Time bin
    selectedTimeBin,
    // Sankey selections
    selectedZone, selectedAction, selectedOutcome,
    // KDE
    isKdeAnimating, kdeCurrentIndex, playSpeed,
    // Tracking
    lastChangeSource,
    // Derived (legacy)
    selectedSeason, entityLabel,
    // Actions
    setSlot, setActiveSide,
    setTimeBin, clearTimeBin,
    setZone, setAction, setOutcome,
    clearSankeySelections, clearAll,
    setKdeIndex, startAnimation, stopAnimation,
  }
})
