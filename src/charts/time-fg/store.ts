import { defineStore } from 'pinia'

// 命名导出，外面才能 import { useTimeFilterStore }
export const useTimeFilterStore = defineStore('timeFilter', {
  state: () => ({
    selectedTimeBin: null,
    selectedBinRange: [],
    timeLinkMode: 'sync',
    timeCurveData: [],
    globalAvgFG: 0
  }),
  actions: {
    setSingleBin(bin) {
      if(this.selectedTimeBin === bin) {
        this.selectedTimeBin = null
        this.selectedBinRange = []
      } else {
        this.selectedTimeBin = bin
        this.selectedBinRange = []
      }
    },
    setBinRange(start, end) {
      this.selectedBinRange = [Math.min(start, end), Math.max(start, end)]
      this.selectedTimeBin = null
    },
    clearTimeFilter() {
      this.selectedTimeBin = null
      this.selectedBinRange = []
    },
    updateCurveData(data) {
      this.timeCurveData = data
      // 旧数据包含 all_made/all_total，新数据只有 left_shot_count/right_shot_count + 各半场 FG%
      // globalAvgFG 用左右半场命中率和出手次数估算加权总命中率（假设每半场 2PT/3PT 各占一半）
      let totalMade = 0, totalShot = 0
      for (const i of data) {
        const leftMade = (i.left_2pt / 100) * (i.left_shot_count / 2) + (i.left_3pt / 100) * (i.left_shot_count / 2)
        const rightMade = (i.right_2pt / 100) * (i.right_shot_count / 2) + (i.right_3pt / 100) * (i.right_shot_count / 2)
        totalMade += leftMade + rightMade
        totalShot += i.left_shot_count + i.right_shot_count
      }
      this.globalAvgFG = totalShot ? +(totalMade / totalShot * 100).toFixed(1) : 0
    }
  }
})
