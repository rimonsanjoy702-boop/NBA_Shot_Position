interface ShotRecord {
  zone_7: string
  shot_type: string
  action_type: string
  made: number
  missed: number
}
interface SeasonData {
  league: {
    shot_records: ShotRecord[]
  }
}
interface FormatParam {
  data: SeasonData
}
interface FormatResult {
  nodes: Array<{ name: string; y: number }>
  links: Array<{ source: string; target: string; value: number }>
  total: number
  avgPct: number
}

// 第一层 Shot Zone 从上到下 y 坐标依次增大（越靠下数字越大）
const ZONE_CONFIG = [
  { name: "Restricted Area (禁区)", y: 0 },
  { name: "In The Paint (Non-RA) (油漆区)", y: 100 },
  { name: "Mid-Range (中距离)", y: 200 },
  { name: "Left Corner 3 (左底角三分)", y: 300 },
  { name: "Right Corner 3 (右底角三分)", y: 400 },
  { name: "Above the Break 3 (弧顶三分)", y: 500 },
  { name: "Backcourt (后场)", y: 600 }
]
// 第二层 Shot Type
const SHOT_TYPE_CONFIG = [
  { name: "2PT Field Goal", y: 200 },
  { name: "3PT Field Goal", y: 400 }
]
// 第三层 Action Type
const ACTION_CONFIG = [
  { name: "Jump Shot (跳投)", y: 100 },
  { name: "Layup / Dunk (上篮/扣篮)", y: 220 },
  { name: "Step Back (后撤步)", y: 340 },
  { name: "Catch & Shoot (接球跳投)", y: 460 }
]
// 第四层 Outcome
const OUTCOME_CONFIG = [
  { name: "出手命中", y: 180 },
  { name: "出手未中", y: 380 }
]

export function formatFourLayer7ZoneSankey({ data }: FormatParam): FormatResult {
  const records = data.league.shot_records
  const links: Array<{ source: string; target: string; value: number }> = []
  let totalAll = 0
  let totalMake = 0

  // 直接拼接带固定y坐标的节点，垂直位置永久锁死
  const nodes = [
    ...ZONE_CONFIG,
    ...SHOT_TYPE_CONFIG,
    ...ACTION_CONFIG,
    ...OUTCOME_CONFIG
  ]

  for (const r of records) {
    const zoneName = r.zone_7
    const shotType = r.shot_type
    const actionType = r.action_type
    const madeNum = r.made
    const missedNum = r.missed
    const totalRow = madeNum + missedNum

    totalAll += totalRow
    totalMake += madeNum

    links.push({ source: zoneName, target: shotType, value: totalRow })
    links.push({ source: shotType, target: actionType, value: totalRow })
    links.push({ source: actionType, target: "出手命中", value: madeNum })
    links.push({ source: actionType, target: "出手未中", value: missedNum })
  }

  const avgPct = totalAll === 0 ? 0 : totalMake / totalAll
  return { nodes, links, total: totalAll, avgPct }
}
