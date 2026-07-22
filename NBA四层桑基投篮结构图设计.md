# NBA 四层桑基投篮结构图设计

> **版本**: v6  
> **最后更新**: 2026-07-22  
> **关联文档**: [多视图交互与联动方案设计](./多视图交互与联动方案设计.md)、[NBA全联盟历年投篮分布桑基图设计](./NBA全联盟历年投篮分布桑基图设计.md)（v1，已废弃）、[Time-FG% 衰减曲线设计](./) 、[Hexbin 热力图设计](./)

---

## 1. 定位与核心分析问题

### 1.1 定位

投篮结构分析页面的主视图，与 Hexbin 热力图并排放置。用桑基图的多阶段分流结构，将 Time-FG% 衰减曲线揭示的"命中率为什么下降"拆解为三个可追踪的因果路径：**区域迁移**、**方式退化**、**手感衰减**。

### 1.2 核心分析问题

1. **命中率下降的机制分解**——比赛末段命中率下降，多大程度是因为"选择了更难的出手区域"（区域迁移），多大程度是因为"同一区域内出手方式退化"（方式退化），多大程度是因为"同一方式的手感变差"（纯粹衰减）？
2. **扣篮的消失曲线**——篮下区域的扣篮占比如何随着比赛推进系统性下降、被上篮所取代？
3. **中距离的配方变化**——中距离在 Q1 是跳投+floater+勾手的混合菜单，到 Q4 是否退化为纯跳投？
4. **三分的单一性诅咒**——三分线外只有跳投一条路径，这如何解释三分命中率对疲劳的高敏感性？
5. **左右半场不对称性**——同一时段，左半场和右半场的出手结构是否存在系统性差异？
6. **宏观时代对比**——1998 赛季 vs 2020 赛季，同一时间段（如 Q4 后段）的投篮结构差异有多大？

### 1.3 与其他四个图表的关系

```
KDE 双峰相变          三分转型分层          Time-FG% 衰减曲线
(宏观距离分布演化)     (球队策略分组)        (比赛内命中率衰减)
       │                    │                      │
       │                    │              ┌───────┴────────┐
       │                    │              │                 │
       └────────────────────┼──────────────┘                 │
                            │                                │
                            ▼                                ▼
                    ┌──────────────┐              ┌──────────────────┐
                    │   桑基图      │◄──双向联动──►│  Time-FG% 衰减曲线 │
                    │   (本设计)    │              │  (L1 时段共享)    │
                    └──────┬───────┘              └──────────────────┘
                           │
                           │ L1点击→Hexbin时段过滤
                           │ L2点击→Hexbin区域高亮
                           ▼
                    ┌──────────────┐
                    │  Hexbin 热力图 │
                    └──────────────┘
```

---

## 2. 四层结构

```
L1: 场次时间 (8)    L2: 出手区域 (7)          L3: 出手方式 (5)    L4: 结果 (2)
───────────────     ───────────────────       ──────────────      ────────────
Q1前 ┐              ┌ Restricted Area         ┌ Dunk              ┌ 命中 (Made)
Q1后 │              │ Paint (Non-RA)          │ Layup             │
Q2前 │              │ Mid-Range               │ Jump Shot         ├─┤
Q2后 ├──→ 8个 ──→   │ Left Corner 3     ──→  │ Hook Shot   ──→   │ │
Q3前 │              │ Right Corner 3          │ Tip-In            └─┤ 不中 (Missed)
Q3后 │              │ Above the Break 3       └                   │
Q4前 │              └ Backcourt                                   ┘
Q4后 ┘
```

**共 8 + 7 + 5 + 2 = 22 个节点，理论路径 8×7×5×2 = 560 条。实际有效路径约 60-90 条**（大量组合样本量为零或接近零，如 Backcourt×Dunk、Corner 3×Hook Shot）。

---

## 3. 节点定义

### 3.1 L1：场次时间（8 节点）

与 Time-FG% 衰减曲线的 8 段时间分箱完全一致。

| 索引 | 标签 | 说明 |
|------|------|------|
| 0 | Q1 前段 | 第1节前6分钟 |
| 1 | Q1 后段 | 第1节后6分钟 |
| 2 | Q2 前段 | 第2节前6分钟 |
| 3 | Q2 后段 | 第2节后6分钟 |
| 4 | Q3 前段 | 第3节前6分钟 |
| 5 | Q3 后段 | 第3节后6分钟 |
| 6 | Q4 前段 | 第4节前6分钟 |
| 7 | Q4 后段 | 第4节后6分钟 |

**视觉编码**：
- 节点位置：左起第一列，从上到下按 Q1前→Q4后 排列
- 节点高度：映射该时段的总出手次数
- 节点颜色：中性灰 `#4E5969`，选中时段用橙色 `#e63946`
- 默认态：全部 8 段展开。点击某段后，被选时段突出显示

### 3.2 L2：出手区域（7 节点）

采用 NBA 官方 Shot Zone Basic 分类，使用 X+Y 二维几何判断（非简化 Y 单轴）。

| 区域 | 几何定义 | 命中率基准 | 叙事角色 |
|------|---------|-----------|---------|
| **Restricted Area** | `√(x²+y²) ≤ 40` 且 `y ≤ 50` | ~60% | 精英终结区，最高效 |
| **Paint (Non-RA)** | `∣x∣ ≤ 80` 且 `y ≤ 140` 且不在 RA 内 | ~42% | 禁区非保护区分，近距离但非精英 |
| **Mid-Range** | 球场内，不在上述区域，`y ≤ 230` | ~39% | 灭绝中的物种 |
| **Left Corner 3** | `y > 230` 且 `x < -220` | ~38% | 最短三分，战术执行产物 |
| **Right Corner 3** | `y > 230` 且 `x > 220` | ~39% | 同上，轻微手性差异 |
| **Above the Break 3** | `y > 230` 且 `∣x∣ ≤ 220` | ~35% | 持球创造三分，个人能力 |
| **Backcourt** | `y > 470` | <3% | 几乎可忽略，存在即故事 |

**视觉编码**：
- 节点位置：左起第二列
- 节点颜色：固定区域色

| 区域 | 颜色 | 色值 |
|------|------|------|
| Restricted Area | 深红 | `#c9381a` |
| Paint (Non-RA) | 橙红 | `#e8733a` |
| Mid-Range | 金黄 | `#f9c74f` |
| Left Corner 3 | 浅绿 | `#72b8a0` |
| Right Corner 3 | 中绿 | `#55a38a` |
| Above the Break 3 | 深青绿 | `#43aa8b` |
| Backcourt | 灰色 | `#aab3bf` |

- 节点高度：映射该区域的总出手次数
- 节点边框深浅：映射该区域平均命中率（越深命中率越高）

### 3.3 L3：出手方式（5 节点）

使用原始数据 Action Type 字段，聚合到 5 个类别。

| 出手方式 | 包含的 Action Type（部分） | 典型距离 | 叙事角色 |
|---------|--------------------------|---------|---------|
| **Dunk** (扣篮) | Dunk, Slam Dunk, Alley Oop Dunk 等 | 0-5ft | 最高命中率，体能消耗大 |
| **Layup** (上篮) | Layup, Driving Layup, Finger Roll 等 | 0-10ft | 篮下主力，Q4替代扣篮 |
| **Jump Shot** (跳投) | Jump Shot, Pullup, Step Back, Fadeaway 等 | 全距离 | 最通用的出手方式，三分唯一方式 |
| **Hook Shot** (勾手) | Hook Shot, Jump Hook, Running Hook 等 | 5-15ft | 内线专属，Paint/中距离 |
| **Tip-In** (补篮) | Tip Shot, Putback 等 | 0-3ft | 二次进攻，仅篮下 |

**视觉编码**：
- 节点位置：左起第三列
- 节点颜色：中性灰 `#A0A4A8`，选中时加粗边框
- 节点高度：映射该方式的总出手次数

**实际可行组合**（区域 × 方式）：
- Restricted Area → Dunk + Layup + Tip-In（扣篮+上篮+补篮）
- Paint Non-RA → Layup + Jump Shot + Hook Shot（上篮+跳投+勾手）
- Mid-Range → Jump Shot + Hook Shot（主要跳投）
- Corner 3 → Jump Shot（几乎唯一方式）
- Above Break 3 → Jump Shot（唯一方式）
- Backcourt → Jump Shot（唯一方式）
- 无意义组合（Dunk×三分、Hook Shot×三分）不生成连线

### 3.4 L4：结果（2 节点）

| 结果 | 含义 |
|------|------|
| **Made** (命中) | `Shot Made Flag = 1` |
| **Missed** (不中) | `Shot Made Flag = 0` |

**视觉编码**：
- 节点位置：左起第四列
- Made 颜色：深绿 `#00B42A`
- Missed 颜色：红色 `#F53F3F`
- 节点高度：映射命中/不中的总次数

---

## 4. 连线（Links）视觉编码

| 数据维度 | 编码方式 | 说明 |
|---------|---------|------|
| 流量大小 | 连线宽度 | count 越大连线越粗 |
| 流向归属 | 颜色继承 L2 | L2→L3 和 L3→L4 的连线颜色继承来源 L2 节点的区域色 |
| 区域效率 | L2 节点边框深浅 | 节点平均 fg_pct 越高边框越深 |
| 时段突出 | L1 节点放大 + 边框 | 选中时段节点放大 15-20%，描边增粗 |

---

## 5. 顶部选择器

桑基图顶部包含三个维度的统一选择器，控制视图的数据范围。选择器为单套（非 Hexbin 的双半场独立选择），因为桑基图是单一视图，半场切换仅为数据过滤维度。

### 5.1 选择器布局

```
┌──────────────────────────────────────────────────────────────────┐
│  🏀 投篮结构桑基图                                               │
│                                                                  │
│  半场: [全部 ▼]    粒度: [联盟 ▼]    赛季: [2019-20 ▼]           │
│         │ 左半场           │ 联盟                                │
│         │ 右半场           │ 球队    ← 粒度=球队时出现实体下拉     │
│         └ 全部             └ 球员    ← 粒度=球员时出现实体下拉     │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 半场维度

控制桑基图展示哪个半场的投篮结构数据。

| 选项 | 数据范围 | 与哪些图表对齐 |
|------|---------|--------------|
| 全部 | X 坐标不限，加载 `data.{scope}.all` | Hexbin 全场热力图的汇总视图 |
| 左半场 | `X < 0` 的投篮，加载 `data.{scope}.left` | Hexbin 左半场、Time-FG% 左半场折线 |
| 右半场 | `X > 0` 的投篮，加载 `data.{scope}.right` | Hexbin 右半场、Time-FG% 右半场折线 |

**交互**：三选一，切换后桑基图直接读取 JSON 中预聚合的 `all`/`left`/`right` 数据块，无需前端重新聚合。

**联动**（后续实现）：切换半场时通过 Pinia store 同步驱动 Time-FG% 对应折线突出 + Hexbin 半场选择。

### 5.3 粒度维度（Scope）

控制数据聚合层级，与 Hexbin 的三级粒度完全一致。

| 选项 | 数据来源 | 实体下拉 |
|------|---------|---------|
| 联盟 | `data.league` | 无 |
| 球队 | `data.teams[{team_id}]` | 显示球队筛选下拉（按名称搜索） |
| 球员 | `data.players[{player_id}]` | 显示球员筛选下拉（按名称搜索） |

**交互**：粒度切换时，如果从「联盟」切到「球队」/「球员」，自动出现实体筛选下拉。切换回「联盟」时实体下拉消失。

### 5.4 赛季维度

23 赛季下拉选择器，选项来自 `ALL_SEASONS`（`src/charts/hexbin/types.ts` 已定义），范围 `1997-98` 到 `2019-20`。

切换赛季触发对应 `sankey_season_{YYYY-YY}.json` 的数据加载。

### 5.5 Demo 阶段简化

Demo 验证阶段选择器降级为：

```
┌──────────────────────────────────────────────────────┐
│  🏀 投篮结构桑基图 · 2019-20 · 联盟                    │
│                                                      │
│  半场: ◉ 全部  ○ 左半场  ○ 右半场                    │
└──────────────────────────────────────────────────────┘
```

- 半场选择器：完整实现（三选一按钮组或下拉）
- 粒度：硬编码「联盟」
- 赛季：硬编码 `2019-20`，仅产出 1 份 JSON

全量数据产出后，再扩展为完整的三维度选择器。

---

## 6. 数据预处理规范

### 6.1 聚合维度

```
time_bin × court_side × shot_zone_basic × action_type_group × shot_made_flag
= 8 × 3 × 7 × 5 × 2
```

理论最大组合数 1680，实际约 200-300 条有样本的有效组合。

### 6.2 JSON 数据结构

文件路径：`public/data/sankey/sankey_season_{YYYY-YY}.json`

```json
{
  "season": "2019-20",
  "league": {
    "all": { "nodes": [...], "links": [...] },
    "left": { "nodes": [...], "links": [...] },
    "right": { "nodes": [...], "links": [...] }
  },
  "teams": {
    "1610612744": {
      "team_name": "Golden State Warriors",
      "abbr": "GSW",
      "all": { "links": [...], "l2_fg_pct": {...} },
      "left": { "links": [...], "l2_fg_pct": {...} },
      "right": { "links": [...], "l2_fg_pct": {...} }
    }
  },
  "players": {
    "76001": {
      "player_name": "Stephen Curry",
      "team_id": 1610612744,
      "team_abbr": "GSW",
      "all": { "links": [...], "l2_fg_pct": {...} },
      "left": { "links": [...], "l2_fg_pct": {...} },
      "right": { "links": [...], "l2_fg_pct": {...} }
    }
  }
}
```

**关键设计决策——teams/players 不存 nodes，仅存 links + l2_fg_pct**：

22 个节点 ID 是全局常量（L1_0~L1_7, L2_RA~L2_BC, L3_Dunk~L3_Tip, L4_Made/Missed），id、layer、label、color 对任何实体都相同。唯一随实体变化的是 size 和 L2 命中率：
- **size**：可由 links 推导（对每列节点，sum(以其为 source/target 的 link.value)）
- **L2 fg_pct**：无法仅从 links 推导（L2→L3 的命中信息在聚合中丢失），因此单独存 `l2_fg_pct` 字段

此优化将单赛季 JSON 从 ~20MB 降至约 0.3–1.5MB（取决于球员数量），23 赛季总计从 ~460MB 降至 ~15–20MB。

**紧凑输出格式**：预处理脚本使用 `json.dump(..., separators=(',', ':'))` 输出紧凑 JSON，不添加缩进空白，进一步节省 40-50% 体积。

### 6.3 节点记录

仅存储在 `league.{side}.nodes` 中，作为全局模板。22 个节点，每层固定：

```typescript
interface SankeyNode {
  id: string;          // "L1_0", "L1_1", ..., "L2_RA", "L2_Paint", ...,
                        // "L3_Dunk", "L3_Layup", ..., "L4_Made", "L4_Missed"
  layer: 1 | 2 | 3 | 4;
  label: string;       // "Q1前", "Restricted Area", "Dunk", "Made"
  size: number;        // 该节点的总出手数（联盟级别）
  meta?: {
    fg_pct?: number;   // L2 节点附命中率
    color?: string;    // L2 节点附区域色
    time_index?: number; // L1 节点附时段索引
  };
}
```

### 6.4 连线记录

**JSON 存储格式（数组编码）**：为节省文件体积，JSON 中 link 使用三元素数组 `[source, target, value]` 而非对象。前端加载后解包为对象使用。

```typescript
// JSON 中的原始格式
type RawSankeyLink = [string, string, number];  // [source, target, value]

// 前端加载后转换为对象
interface SankeyLink {
  source: string;      // 源节点 id
  target: string;      // 目标节点 id
  value: number;       // 流量（出手次数）
}
```

**前端解码**（sankey-data.ts）：
```typescript
function decodeLinks(raw: [string, string, number][]): SankeyLink[] {
  return raw.map(([source, target, value]) => ({ source, target, value }))
}
```

### 6.5 数据过滤阈值

| 层级 | 最小 count | 说明 |
|------|-----------|------|
| 联盟/球队 | ≥ 5 | 过滤无效细流量 |
| 单球员 | ≥ 3 | 球员样本量小 |
| Backcourt | ≥ 1 | 保留存在即有价值 |

### 6.6 前端 entities 节点重建逻辑

前端加载 entity（球队/球员）数据时，从 league 的 nodes 模板 + entity 的 links 重建完整 nodes：

```typescript
function reconstructEntityData(
  leagueNodes: SankeyNode[],   // 模板（id/label/layer/color）
  entityLinks: SankeyLink[],   // entity 的连线
  l2FgPct: Record<string, number>,  // entity 的 L2 命中率 map
): { nodes: SankeyNode[]; links: SankeyLink[] } {
  // 1. 从 links 推导各节点 size
  const sizeMap: Record<string, number> = {};
  for (const link of entityLinks) {
    // source 节点流出 = link.value
    sizeMap[link.source] = (sizeMap[link.source] || 0) + link.value;
    // target 节点流入也计入（L1 只有流出，L4 只有流入）
  }

  // 2. 用 league 模板克隆节点，覆盖 size 和 fg_pct
  const nodes = leagueNodes.map(n => {
    const node = { ...n, size: sizeMap[n.id] || 0 };
    if (n.layer === 2 && l2FgPct) {
      // L2 节点：覆盖 fg_pct 为 entity 自己的
      const zoneKey = n.id.replace('L2_', '');
      node.meta = { ...n.meta, fg_pct: l2FgPct[zoneKey] ?? n.meta?.fg_pct };
    }
    return node;
  }).filter(n => n.size > 0);  // 去掉 size=0 的节点（如某队没有后场投篮）

  return { nodes, links: entityLinks };
}
```

**推导正确性保证**：
- L1 节点 size = sum(以其为 source 的 L1→L2 link.value)（L1 只流出）
- L2 节点 size = max(sum 流出, sum 流入)（两端相等，取其一即可）
- L3 节点 size = sum(以其为 source 的 L3→L4 link.value)（L3 只流出）
- L4 节点 size = sum(以其为 target 的 L3→L4 link.value)（L4 只流入）
- L2 fg_pct：从 `l2_fg_pct` 直接读取（预处理阶段计算好）

### 6.7 l2_fg_pct 字段说明

```typescript
// 7 个 L2 区域的命中率，key 为 zone 短码
interface L2FgPctMap {
  "RA": number;     // Restricted Area 命中率
  "Paint": number;  // Paint (Non-RA) 命中率
  "MR": number;     // Mid-Range 命中率
  "LC3": number;    // Left Corner 3 命中率
  "RC3": number;    // Right Corner 3 命中率
  "AB3": number;    // Above the Break 3 命中率
  "BC": number;     // Backcourt 命中率
}
```

JSON 中每个 entity 的每个 court_side 块附带一个 `l2_fg_pct` 对象，7 个 key，约 200 bytes。此字段存在的唯一原因是：**L2 区域命中率 = 该区域中 Made/(Made+Missed)，而 links 只有两两层级之间的流量，L2→L3 这一步丢失了命中/不中信息，无法仅从 links 反向算出**。

## 7. Pinia Store 扩展

在已有 `timeFilter` store 基础上，增加桑基图需要的状态字段。

```typescript
// stores/sankeyContext.ts
import { defineStore } from 'pinia'

export const useSankeyStore = defineStore('sankey', {
  state: () => ({
    // ═══ 桑基图专属 ═══
    selectedCourtSide: 'all' as 'left' | 'right' | 'all',
    selectedZone: null as string | null,       // L2 区域 id
    selectedShotType: null as string | null,   // L3 出手方式 id
    selectedOutcome: null as string | null,    // L4 结果 id

    // ═══ 共享（复用 timeFilter store 的 selectedTimeBin） ═══
    // selectedTimeBin 来自 useTimeFilterStore
    // selectedSeason 来自全局 analysisContext
    // selectedTeamId / selectedPlayerId 来自全局 analysisContext
  }),
  actions: {
    setCourtSide(side: 'left' | 'right' | 'all') {
      this.selectedCourtSide = side
    },
    clickZone(zoneId: string | null) {
      this.selectedZone = this.selectedZone === zoneId ? null : zoneId
      // 点击 L2 节点时联动清空 L3 选择
      if (zoneId) this.selectedShotType = null
    },
    clickShotType(typeId: string | null) {
      this.selectedShotType = this.selectedShotType === typeId ? null : typeId
    },
    clickOutcome(outcomeId: string | null) {
      this.selectedOutcome = this.selectedOutcome === outcomeId ? null : outcomeId
    },
    clearAll() {
      this.selectedCourtSide = 'all'
      this.selectedZone = null
      this.selectedShotType = null
      this.selectedOutcome = null
    }
  }
})
```

---

## 8. 联动矩阵

### 8.1 联动一览

| # | 触发源 | 目标 | 方向 | 行为 |
|---|--------|------|------|------|
| LK-1 | Time-FG% 点击时段 | 桑基 L1 | → | 桑基 L1 对应节点突出显示 |
| LK-2 | 桑基 L1 点击 | Time-FG% | ← | Time-FG% 对应数据点高亮 + 十字准线 |
| LK-3 | 桑基 L1 点击 | Hexbin | → | Hexbin 过滤为该时段的投篮数据 |
| LK-4 | 桑基 L2 点击 | Hexbin | → | Hexbin 中对应区域的格点突出显示 |
| LK-5 | 桑基 L2 hover | KDE | → | KDE 图对应距离段加背景色带 |
| LK-6 | 桑基 L2 hover | 三分转型 | → | 仅 L2=三分区域时，三分转型图 3PAr 标签高亮 |
| LK-7 | 桑基半场切换 | Time-FG% | → | Time-FG% 对应左右半场折线突出 |
| LK-8 | 桑基半场切换 | Hexbin | → | Hexbin 对应半场选择同步 |

### 8.2 LK-1 / LK-2：Time-FG% ↔ 桑基（双向）

```
用户点击 Time-FG% 的 "Q4后" 数据点:
  → Pinia selectedTimeBin = 7
  → 桑基 L1=Q4后 节点突出显示
  → 其他 L1 节点保持可见但不突出

用户点击桑基 L1=Q4后 节点:
  → Pinia selectedTimeBin = 7
  → Time-FG% 图 Q4后 数据点突出 + 十字准线定位
```

**双向绑定**：两个视图通过同一个 `selectedTimeBin` 状态驱动，任一触发另一方自动响应。

### 8.3 LK-3：桑基 L1 → Hexbin 时段过滤

```
点击桑基 L1=Q4后
  → Hexbin 调用 extractHexbins(data, scope, entityId, timeBin=7)
  → 热力图仅展示 Q4 后段投篮的六边形格点
  → Hexbin 标题更新："Q4 后段 · 2019-20 · 联盟"
```

数据已存在于 `hexbins_by_time` 中，无需额外预处理。

### 8.4 LK-4：桑基 L2 → Hexbin 区域高亮

```
点击桑基 L2=Above the Break 3
  → Hexbin 遍历所有 cells
  → cells 中 y>230 且 |x|≤220 的格点 → 突出显示
  → 其他格点 → 保持正常

点击桑基 L2=Restricted Area
  → Hexbin cells 中 √(x²+y²)≤40 的格点 → 突出显示
```

| 桑基 L2 节点 | Hexbin 高亮条件 |
|-------------|----------------|
| Restricted Area | `√(x²+y²) ≤ 40` |
| Paint (Non-RA) | `∣x∣ ≤ 80 ∧ y ≤ 140` 且不在 RA 内 |
| Mid-Range | 球场内，不在上述区域，`y ≤ 230` |
| Left Corner 3 | `y > 230 ∧ x < -220` |
| Right Corner 3 | `y > 230 ∧ x > 220` |
| Above the Break 3 | `y > 230 ∧ ∣x∣ ≤ 220` |
| Backcourt | `y > 470`（预期无格点，高亮操作为空） |

### 8.5 LK-5：桑基 L2 → KDE 距离段高亮

```
hover 桑基 L2=Restricted Area  → KDE 0-5ft 段背景加 RA 色 (#c9381a)
hover 桑基 L2=Mid-Range        → KDE 5-23ft 段背景加中距离色 (#f9c74f)
hover 桑基 L2=Above Break 3    → KDE 23ft+ 段背景加三分色 (#43aa8b)
```

**映射规则**：L2 区域 → 投篮距离范围 → KDE X 轴色带。

| L2 | 距离范围 |
|----|---------|
| Restricted Area + Paint | 0-10 ft |
| Mid-Range | 10-23 ft |
| Corner 3 + Above Break 3 | 23-30 ft |
| Backcourt | 30+ ft |

### 8.6 LK-7 / LK-8：半场切换联动

```
桑基切换 "半场: 左半场"
  → Time-FG%: 左半场两分/三分折线突出，右半场折线淡化
  → Hexbin: 若 Hexbin 左右选择器存在，左侧 Hexbin 跟随到左半场
```

---

## 9. SVG 画布布局

### 9.1 整体结构

```svg
<svg viewBox="0 0 1600 900">
  <!-- 底层：背景底色 -->
  <g id="base-bg"></g>
  
  <!-- 中层：桑基基础结构 -->
  <g id="sankey-links">
    <!-- L1→L2 连线 -->
    <!-- L2→L3 连线 -->
    <!-- L3→L4 连线 -->
  </g>
  <g id="sankey-nodes">
    <!-- L1 节点列 (x≈100) -->
    <!-- L2 节点列 (x≈450) -->
    <!-- L3 节点列 (x≈800) -->
    <!-- L4 节点列 (x≈1150) -->
  </g>
  
  <!-- 上层：文字与UI叠加 -->
  <g id="node-text"> 节点标签、数值文字 </g>
  <g id="ui-overlay"> 图例、悬浮提示 </g>
</svg>
```

### 9.2 节点列布局

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Q1前 ───┬── RA ───────┬── Dunk ───────┬── Made     │
│          │             │               │            │
│  Q1后 ───┤── Paint ────┤── Layup ──────┤            │
│          │             │               │            │
│  Q2前 ───┤── Mid-Range ├── Jump Shot ──┤            │
│          │             │               ├── Missed ──┤
│  Q2后 ───┤── LC3 ──────┤── Hook ───────┤            │
│          │             │               │            │
│  Q3前 ───┤── RC3 ──────┘── Tip-In ─────┘            │
│          │                                           │
│  Q3后 ───┤── AB3                                    │
│          │                                           │
│  Q4前 ───┤── Backcourt                              │
│          │                                           │
│  Q4后 ───┘                                           │
│                                                      │
│   x: 100         450            800          1150    │
│   L1              L2             L3           L4     │
└──────────────────────────────────────────────────────┘
```

---

## 10. 交互模式

### 10.1 默认态

- 8 个 L1 节点全部显示，L1→L2→L3→L4 四层连线全部可见
- L2 节点按区域色着色，连线颜色从 L2 继承
- 全部时段可见，作为参考全景

### 10.2 点击 L1 节点

- 被点击的 L1 节点突出显示
- 被点击 L1 节点对应的 L1→L2 子图突出显示（连线增粗、颜色饱和）
- 其他 L1 节点及其子图淡化
- Pinia `selectedTimeBin` 更新 → Time-FG% 和 Hexbin 同步响应

### 10.3 点击 L2 节点

- 被点击的 L2 节点突出显示
- 该节点的 L2→L3→L4 下游子图突出显示
- Hexbin 对应区域格点突出显示
- 再次点击取消选中

### 10.4 点击 L3 节点

- 被点击的 L3 节点突出显示
- 该节点的 L3→L4 下游子图突出显示
- 再次点击取消选中

### 10.5 点击 L4 节点

- 被点击的 L4 节点突出显示
- 再次点击取消选中

### 10.6 Hover 通用行为

- Hover 任意节点或连线 → 显示 tooltip（节点名、count、fg_pct）
- Hover L2 节点 → 联动 KDE、三分转型图

---

## 11. 文件结构

```
src/
├── stores/
│   └── sankeyContext.ts              ← 桑基图 Pinia Store
├── charts/
│   └── sankey/
│       ├── SankeyPage.vue            ← 桑基图页面容器（含顶部选择器）
│       ├── SankeyChart.vue           ← SVG 桑基图核心组件
│       ├── sankey-layout.ts          ← 节点定位 + 连线路径计算
│       ├── sankey-data.ts            ← 数据加载 + zone 分类工具函数
│       └── types.ts                  ← 类型定义
├── pages/
│   └── ShotStructurePage.vue         ← Page 3: 桑基图 + Hexbin
public/
└── data/
    └── sankey/
        ├── sankey_season_1997-98.json
        ├── sankey_season_1998-99.json
        ├── ...
        └── sankey_season_2019-20.json   ← 共 23 个文件
```

---

## 12. 上线前数据核验清单

- [ ] 23 份赛季 JSON 文件全部生成，无空文件、损坏文件
- [ ] 每份文件包含 `all`、`left`、`right` 三组半场数据
- [ ] `shot_zone_basic` 分类覆盖全部 7 区，无遗漏
- [ ] `action_type` 聚合到 5 个 L3 类别，映射表完整
- [ ] 所有 `fg_pct` 数值在 0~1 区间，保留 3 位小数
- [ ] 最小 count 过滤阈值生效（联盟/球队≥5，球员≥3）
- [ ] 全部数据文件总存储体积 ≤ 15MB
- [ ] L1 时段索引与 Time-FG% 的 8 段标签严格对应
- [ ] Left/Right Corner 3 分割线（|x|=220）验证无误
- [ ] Backcourt 区域数据不丢失（count≥1 即可保留）

---

## 13. 实现优先级

| 优先级 | 内容 | 说明 |
|-------|------|------|
| **P0** | 四层桑基图核心组件 + 7区 L2 | SVG 手绘，不依赖 ECharts sankey |
| **P0** | 数据预处理脚本 (23赛季 JSON) | 8时段×3半场×7区域×5方式×2结果 |
| **P0** | 半场切换选择器 | all/left/right 三选一 |
| **P0** | LK-1/2: Time-FG% ↔ 桑基双向联动 | Pinia `selectedTimeBin` 共享 |
| **P0** | LK-3: 桑基 L1 → Hexbin 时段过滤 | `hexbins_by_time` 已有 |
| **P0** | LK-4: 桑基 L2 → Hexbin 区域高亮 | X+Y 几何判断，前端视觉层 |
| **P1** | LK-5: 桑基 L2 → KDE 距离段高亮 | 区域→距离范围映射 |
| **P1** | LK-7/8: 半场切换 → Time-FG% + Hexbin | 左右半场数据联动 |
| **P1** | Pinia sankeyContext store | 与 timeFilter + analysisContext 协作 |
| **P2** | LK-6: 桑基 L2 → 三分转型联动 | 仅三分区域节点触发 |
| **P2** | 赛季/球队/球员全局选择器对接 | 复用 analysisContext store |
