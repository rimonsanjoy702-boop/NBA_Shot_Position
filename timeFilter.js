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
      const totalMade = data.reduce((s, i)=>s+i.all_made,0)
      const totalShot = data.reduce((s, i)=>s+i.all_total,0)
      this.globalAvgFG = totalShot ? (totalMade / totalShot * 100).toFixed(1) : 0
    }
  }
})
