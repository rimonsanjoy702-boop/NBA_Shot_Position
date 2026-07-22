import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAnalysisContext = defineStore('analysisContext', () => {
  // ═══ 跨页共享 ═══
  const selectedSeason = ref<string>('2019-20')
  const selectedTeamId = ref<number | null>(null)
  const selectedTeamName = ref<string | null>(null)
  const selectedPlayerId = ref<number | null>(null)
  const selectedPlayerName = ref<string | null>(null)

  // ═══ Page1 专属: 空间探索 ═══
  const selectedTimeBin = ref<number | null>(null)
  const timeLinkMode = ref<'sync' | 'independent'>('sync')

  // ═══ Page2 专属: 演化趋势 ═══
  const isKdeAnimating = ref(false)
  const kdeCurrentIndex = ref(22)
  const playSpeed = ref(1)

  // ═══ Page3 专属: 投篮结构 ═══
  const selectedZone = ref<string | null>(null)
  const selectedShotType = ref<'2PT' | '3PT' | null>(null)

  // ═══ 联动追踪 ═══
  const lastChangeSource = ref<string>('init')

  // ═══ 当前实体标签 ═══
  const entityLabel = computed(() => {
    if (selectedPlayerName.value) return { text: selectedPlayerName.value, type: 'player' as const }
    if (selectedTeamName.value) return { text: selectedTeamName.value, type: 'team' as const }
    return { text: '联盟平均', type: 'league' as const }
  })

  // ═══ Actions ═══
  function setSeason(season: string, source: string) {
    lastChangeSource.value = source
    selectedSeason.value = season
  }

  function setTeam(teamId: number, teamName: string, source: string) {
    lastChangeSource.value = source
    selectedTeamId.value = teamId
    selectedTeamName.value = teamName
    selectedPlayerId.value = null
    selectedPlayerName.value = null
  }

  function setPlayer(playerId: number, playerName: string, source: string) {
    lastChangeSource.value = source
    selectedPlayerId.value = playerId
    selectedPlayerName.value = playerName
    selectedTeamId.value = null
    selectedTeamName.value = null
  }

  function clearEntity(source: string) {
    lastChangeSource.value = source
    selectedTeamId.value = null
    selectedTeamName.value = null
    selectedPlayerId.value = null
    selectedPlayerName.value = null
  }

  function setTimeBin(bin: number | null, source: string) {
    lastChangeSource.value = source
    selectedTimeBin.value = bin
  }

  function setZone(zone: string | null, source: string) {
    lastChangeSource.value = source
    selectedZone.value = zone
  }

  function setShotType(type: '2PT' | '3PT' | null, source: string) {
    lastChangeSource.value = source
    selectedShotType.value = type
  }

  function setKdeIndex(index: number, source: string) {
    lastChangeSource.value = source
    kdeCurrentIndex.value = index
  }

  function startAnimation() { isKdeAnimating.value = true }
  function stopAnimation() { isKdeAnimating.value = false }

  return {
    selectedSeason, selectedTeamId, selectedTeamName,
    selectedPlayerId, selectedPlayerName,
    selectedTimeBin, timeLinkMode,
    isKdeAnimating, kdeCurrentIndex, playSpeed,
    selectedZone, selectedShotType,
    lastChangeSource, entityLabel,
    setSeason, setTeam, setPlayer, clearEntity,
    setTimeBin, setZone, setShotType, setKdeIndex,
    startAnimation, stopAnimation,
  }
})
