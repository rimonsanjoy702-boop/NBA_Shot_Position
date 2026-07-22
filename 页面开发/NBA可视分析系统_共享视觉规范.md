# NBA 投篮可视分析系统 · 共享视觉规范 v1.0

> 适用范围：Hexbin 热力图、KDE 双峰相变、三分采纳曲线 三个模块
> 核心理念：**深色沉浸 · 信息优先 · 体育数据的冷静感**

---

## 目录

1. [设计原则](#1-设计原则)
2. [色板系统](#2-色板系统)
3. [字体体系](#3-字体体系)
4. [间距与圆角](#4-间距与圆角)
5. [图表公共样式](#5-图表公共样式)
6. [组件状态规范](#6-组件状态规范)
7. [页面布局模板](#7-页面布局模板)
8. [CSS 变量定义](#8-css-变量定义)
9. [核验清单](#9-核验清单)

---

## 1. 设计原则

| 原则 | 含义 | 反例 |
|------|------|------|
| **深色为主** | 全系统深色背景，减少视觉疲劳，突出数据发光感 | 白色背景 + 高饱和图表 |
| **信息优先** | 装饰服务于数据，不喧宾夺主 | 大面积渐变、无意义的动画 |
| **一致编码** | 同一语义在所有模块中用同一颜色 | 热力图里命中=绿，桑基图里命中=蓝 |
| **冷静克制** | 用灰度和低饱和色表达中性信息，亮色仅用于强调 | 所有元素都用高饱和色争抢注意力 |
| **即时可读** | 任何人（包括评委）3 秒内理解图表在展示什么 | 需要反复看 legend 才懂 |

---

## 2. 色板系统

### 2.1 背景色

| Token | 色值 | 用途 | 示例场景 |
|-------|------|------|---------|
| `--bg-root` | `#0d1117` | 页面根背景 | `<body>` / 最外层容器 |
| `--bg-card` | `rgba(255,255,255,0.04)` | 卡片/面板背景 | 图表容器、控制栏、统计卡片 |
| `--bg-card-hover` | `rgba(255,255,255,0.07)` | 卡片悬停态 | 可点击的统计卡片 hover |
| `--bg-input` | `rgba(255,255,255,0.06)` | 输入控件背景 | 下拉框、搜索框 |
| `--bg-overlay` | `rgba(0,0,0,0.75)` | 遮罩层 | 模态框背景、全屏加载 |

### 2.2 边框与分隔

| Token | 色值 | 用途 |
|-------|------|------|
| `--border-card` | `rgba(255,255,255,0.08)` | 卡片/面板边框 |
| `--border-input` | `rgba(255,255,255,0.12)` | 输入控件边框 |
| `--border-hover` | `rgba(255,255,255,0.25)` | 悬停边框 |
| `--border-active` | `rgba(52,152,219,0.45)` | 激活/聚焦边框（蓝色） |
| `--divider` | `rgba(255,255,255,0.06)` | 列表/菜单分隔线 |

### 2.3 文字色

| Token | 色值 | 用途 |
|-------|------|------|
| `--text-primary` | `#e6edf3` | 主标题、重要数据、当前选中项 |
| `--text-secondary` | `#8b949e` | 副标题、标签、辅助说明 |
| `--text-tertiary` | `#5c6670` | 占位符、禁用态文字 |
| `--text-inverse` | `#0d1117` | 在亮色按钮/标签上的深色文字 |

### 2.4 语义色（固定含义，全系统一致）

| Token | 色值 | 语义 | 所有模块中的含义 |
|-------|------|------|-----------------|
| `--semantic-made` | `#00d2a0` | 命中 / 成功 / 正向 | 投篮命中、胜率上升、趋势向好 |
| `--semantic-missed` | `#ff6b6b` | 未中 / 失败 / 负向 | 投篮未中、胜率下降、趋势衰退 |
| `--semantic-three` | `#3498db` | 三分 / 外线 | 三分出手、三分命中率、三分区域 |
| `--semantic-two` | `#f39c12` | 两分 / 内线（非禁区） | 两分出手、中距离区域 |
| `--semantic-rim` | `#e74c3c` | 禁区 / 篮下 | 禁区出手、近筐区域 |
| `--semantic-midrange` | `#8b949e` | 中距离 / 低效区 | 中距离出手、正在消失的区域 |

### 2.5 功能色

| Token | 色值 | 用途 |
|-------|------|------|
| `--accent-primary` | `#3498db` | 主强调色（选中、聚焦、CTA 按钮） |
| `--accent-secondary` | `#f39c12` | 次强调色（高亮、通知） |
| `--accent-highlight` | `#ffffff` | 最大强调（当前播放帧、激活态曲线） |
| `--chart-grid` | `rgba(255,255,255,0.06)` | 图表网格线 |
| `--chart-axis` | `rgba(255,255,255,0.15)` | 图表轴线 |

### 2.6 数据色阶

#### 命中率色阶（热力图、区域着色）

```
0% ─────────────────────────────── 100%
低效                    中效                    高效
#ff6b6b → #f4a460 → #f4d03f → #5cdb8b → #00d2a0
 红         橙        黄        绿       翠绿
```

| 命中率区间 | 色值 | 含义 |
|-----------|------|------|
| 0% – 30% | `#ff6b6b` | 非常低效 |
| 30% – 40% | `#f4a460` | 低效 |
| 40% – 50% | `#f4d03f` | 中等 |
| 50% – 60% | `#5cdb8b` | 高效 |
| 60% – 100% | `#00d2a0` | 非常高效 |

#### 密度色阶（Hexbin 大小 / 密度）

```
稀疏 ──────────────────────→ 密集
rgba(52,152,219,0.10) → rgba(52,152,219,0.85)
```

> 使用单色渐变（蓝色 opacity），避免与命中率色阶（红绿）混淆。

### 2.7 球队/球员分类色

用于三分采纳曲线（先行者 / 中期 / 落后者）：

| 分类 | 色值 | 说明 |
|------|------|------|
| 先行者（Early Adopters） | `#00d2a0` | 翠绿 — 正向、领先 |
| 中期采纳者（Majority） | `#f4d03f` | 金黄 — 中性、随大流 |
| 落后者（Laggards） | `#8b949e` | 灰色 — 滞后、低活跃 |

---

## 3. 字体体系

### 3.1 字体栈

```css
font-family:
  -apple-system, BlinkMacSystemFont,
  'Segoe UI', Roboto, 'Helvetica Neue', Arial,
  'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei',
  sans-serif;
```

> 优先使用系统原生字体，确保中英文混排质量。不引入 Web Font，减少加载时间。

### 3.2 字号与字重

| Token | 字号 | 字重 | 用途 | 示例 |
|-------|------|------|------|------|
| `--fs-hero` | 32px | 800 | 页面大标题 | "🏀 投篮距离分布演化" |
| `--fs-title` | 20px | 700 | 模块标题 / 卡片标题 | "KDE 密度曲线" |
| `--fs-subtitle` | 14px | 400 | 副标题 / 描述文字 | "4,729,512 次投篮 · 24 个赛季" |
| `--fs-body` | 13px | 400 | 正文 / 表格内容 / tooltip 正文 | — |
| `--fs-label` | 12px | 600 | 轴标签 / 图例 / 按钮文字 | X 轴"投篮距离 (ft)" |
| `--fs-caption` | 11px | 400 | 辅助说明 / 脚注 | "按 ← → 方向键逐帧浏览" |
| `--fs-stat` | 30px | 800 | 统计卡片大数字 | "6.8" |
| `--fs-stat-delta` | 11px | 600 | 统计卡片变化量 | "vs 1998: +1.3" |

### 3.3 行高

| Token | 值 | 用途 |
|-------|-----|------|
| `--lh-heading` | 1.2 | 标题 |
| `--lh-body` | 1.5 | 正文、描述 |
| `--lh-compact` | 1.1 | 统计数字、标签 |

---

## 4. 间距与圆角

### 4.1 间距标尺（基于 4px 网格）

| Token | 值 | 用途 |
|-------|-----|------|
| `--space-xs` | 4px | 图标与文字间距、紧凑内边距 |
| `--space-sm` | 8px | 同类元素间距、卡片内边距 |
| `--space-md` | 16px | 卡片间距、区块间距 |
| `--space-lg` | 24px | 大区块间距、页面主要分段 |
| `--space-xl` | 32px | 页面外边距 |
| `--space-2xl` | 48px | 顶级区块分隔 |

### 4.2 圆角

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-sm` | 4px | 按钮、标签、输入框 |
| `--radius-md` | 8px | 控制栏、工具栏 |
| `--radius-lg` | 10px | 图表卡片、统计卡片、面板 |
| `--radius-full` | 9999px | 头像、标签胶囊、开关 |

---

## 5. 图表公共样式

### 5.1 ECharts 全局默认

以下配置作为所有 ECharts 图表的基准：

```javascript
// 所有图表 share 的基准 option
const BASE_CHART_OPTION = {
  backgroundColor: 'transparent',

  // 网格
  grid: {
    left: 48,
    right: 48,
    top: 20,
    bottom: 36,
    containLabel: false,
  },

  // 提示框
  tooltip: {
    trigger: 'axis',              // 或 'item'（饼图/散点图用 item）
    backgroundColor: 'rgba(13,17,23,0.95)',
    borderColor: 'rgba(255,255,255,0.1)',
    borderWidth: 1,
    padding: [10, 14],
    textStyle: {
      color: '#e6edf3',
      fontSize: 13,
      fontFamily: 'inherit',
    },
    extraCssText: 'border-radius: 8px; backdrop-filter: blur(8px);',
  },

  // 图例
  legend: {
    textStyle: { color: '#8b949e', fontSize: 12 },
    icon: 'roundRect',
    itemWidth: 10,
    itemHeight: 10,
    itemGap: 20,
  },

  // X 轴
  xAxis: {
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
    axisTick: { show: false },
    axisLabel: { color: '#8b949e', fontSize: 11 },
    splitLine: { show: false },
    nameTextStyle: { color: '#8b949e', fontSize: 12 },
  },

  // Y 轴
  yAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#8b949e', fontSize: 11 },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    nameTextStyle: { color: '#8b949e', fontSize: 12 },
  },

  // 动画
  animation: true,
  animationDuration: 400,
  animationEasing: 'cubicInOut',
}
```

### 5.2 Tooltip 内容格式

#### 时序/折线图 tooltip

```
┌─────────────────────────────┐
│ 距离: 15.0 ft               │  ← 加粗标题（当前 X 值）
│                             │
│ ● 1997-98 (早期)  12.4 ×10⁻³│  ← 圆点 + 系列名 + 值
│ ● 2019-20 (近期)   5.1 ×10⁻³│
│ ● 2015-16 (当前)   8.9 ×10⁻³│  ← 当前赛季高亮
└─────────────────────────────┘
```

#### 柱状图 tooltip

```
┌─────────────────────────────┐
│ 2015-16                     │  ← 加粗标题
│                             │
│ 双峰指数: 6.8              │  ← 主要指标高亮色
│ 篮下占比: 33%              │
│ 中距离占比: 19%            │
│ 三分占比: 24%              │
│ 出手数: 207K               │
└─────────────────────────────┘
```

#### 热力图/散点图 tooltip

```
┌─────────────────────────────┐
│ 弧顶三分 (Above Break 3)   │  ← 区域名
│                             │
│ 命中率: 34.9%              │
│ 出手次数: 12,847           │
│ 占该区域出手: 8.2%         │
└─────────────────────────────┘
```

### 5.3 图例规范

| 规范项 | 规则 |
|--------|------|
| 位置 | 图表底部居中（`bottom: 8, left: 'center'`） |
| 样式 | 圆角矩形图标（`icon: 'roundRect'`），宽 10px 高 10px |
| 布局 | 水平排列，间距 ≥ 20px |
| 字号 | 12px，字色 `--text-secondary` |
| 数量限制 | ≤ 6 项直接展示；> 6 项启用滚动或分页 |

### 5.4 响应式断点

| 断点 | 最小宽度 | 行为 |
|------|---------|------|
| 桌面 | 1280px | 完整布局：主图 + 侧面板 + 底部图 |
| 平板 | 768px | 卡片和图表纵向堆叠，侧面板移到底部 |
| 手机 | — | 不支持，最低要求 1280px 桌面浏览 |

### 5.5 动画规范

| 动画类型 | 时长 | 缓动 | 说明 |
|----------|------|------|------|
| 图表数据过渡 | 400ms | `cubicInOut` | 切换赛季时曲线的平滑过渡 |
| 滑块拖动 | 0ms（实时） | — | 直接绑定 v-model，无延迟 |
| 播放帧切换 | 500ms（1× 速度） | — | 定时器间隔，非 CSS 动画 |
| 卡片数值变化 | 200ms | `ease-out` | 数字跳动过渡（可选 CSS transition） |
| 悬停反馈 | 150ms | `ease-out` | 按钮/卡片背景色过渡 |
| Tooltip 出现 | 即时 | — | ECharts 默认行为，不改动 |

---

## 6. 组件状态规范

### 6.1 加载态

#### 全页加载

```
┌──────────────────────────────────────────────┐
│                                              │
│                                              │
│              ◜ ◝                             │
│              ◟ ◞  旋转圆环                   │
│                   颜色: --accent-primary      │
│                   线宽: 3px                   │
│                   尺寸: 40×40px               │
│                                              │
│          加载数据中...                        │
│          颜色: --text-secondary              │
│          字号: 14px                          │
│                                              │
└──────────────────────────────────────────────┘
```

实现：一个 40px 圆环，`border: 3px solid rgba(255,255,255,0.1)` + `border-top-color: #3498db`，CSS `animation: spin 0.8s linear infinite`。

#### 局部加载（图表内）

使用 ECharts 内置 `showLoading()`：

```javascript
chart.showLoading({
  text: '加载中...',
  color: '#3498db',
  textColor: '#8b949e',
  maskColor: 'rgba(13,17,23,0.75)',
  zlevel: 0,
})
```

### 6.2 空数据态

当筛选条件无匹配数据时（如某球员在某赛季无投篮记录）：

```
┌──────────────────────────────────────────────┐
│                                              │
│              🏀                              │
│          暂无投篮数据                         │
│          颜色: --text-secondary              │
│          字号: 14px                          │
│                                              │
│    该筛选条件下没有投篮记录                    │
│    颜色: --text-tertiary                     │
│    字号: 12px                                │
│                                              │
│        [清除筛选条件]                         │
│        按钮: --accent-primary 边框            │
│                                              │
└──────────────────────────────────────────────┘
```

实现：各组件内部判断数据是否为空数组，空则渲染 `EmptyState` 插槽。

### 6.3 异常态

#### 数据加载失败

```
┌──────────────────────────────────────────────┐
│                                              │
│              ⚠️                              │
│          数据加载失败                         │
│          颜色: --semantic-missed             │
│          字号: 14px                          │
│                                              │
│    无法连接到数据源，请检查网络后重试           │
│    颜色: --text-secondary                    │
│    字号: 12px                                │
│                                              │
│           [重新加载]                          │
│           按钮: --accent-primary              │
│                                              │
└──────────────────────────────────────────────┘
```

实现：`data.ts` 的 `GET()` 函数中 catch 后用 `ElMessage.error()` 弹出通知，同时组件显示 ErrorState。

#### 图表渲染异常

使用 ECharts 的 `renderError` 或 try-catch 包裹 option 计算：

```javascript
try {
  return computedOption.value
} catch (e) {
  console.error('Chart render error:', e)
  return { /* 空白 option + 错误标注 */ }
}
```

### 6.4 交互态

| 状态 | 视觉表现 |
|------|---------|
| **悬停（hover）** | 卡片：边框变亮 (`--border-hover`)；按钮：背景变亮；图表元素：ECharts emphasis 默认 |
| **激活/选中（active）** | 边框色变为 `--border-active`；当前赛季曲线线宽加粗 + 白色；速度按钮选中态蓝底 |
| **按下（press）** | 按钮 scale(0.97)；滑块 thumb 变亮 |
| **禁用（disabled）** | opacity: 0.4，cursor: not-allowed，不响应点击 |
| **聚焦（focus）** | 输入框 `--border-active` + 外发光 `0 0 0 2px rgba(52,152,219,0.3)` |

### 6.5 Tooltip 内容规范

| 规范项 | 规则 | 示例 |
|--------|------|------|
| 标题 | 加粗，首行，14px | `距离: 15.0 ft` |
| 数值格式 | 百分比保留 1 位小数，千位分隔 | `34.9%` / `12,847` |
| 颜色标记 | 圆点与曲线/柱颜色一致 | `● 2015-16` |
| 单位 | 紧跟数值，不加空格 | `207K` `15.0 ft` |
| 最大行数 | ≤ 8 行 | 超出用"... N more" |

---

## 7. 页面布局模板

### 7.1 标准页面结构

```
┌──────────────────────────────────────────────────────────┐
│  页面根容器                                              │
│  min-height: 100vh, background: --bg-root               │
│  padding: 24px 32px 40px                                │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  页面标题区 (可选)                                  │  │
│  │  h1: --fs-hero, --text-primary                     │  │
│  │  p:  --fs-subtitle, --text-secondary               │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  图表卡片                                          │  │
│  │  background: --bg-card                             │  │
│  │  border: 1px solid --border-card                   │  │
│  │  border-radius: --radius-lg                        │  │
│  │  padding: 18px 20px 12px                           │  │
│  │  margin-bottom: 16px                               │  │
│  │                                                    │  │
│  │  ┌─ 卡片标题行 ─────────────────────────────────┐  │  │
│  │  │ ● 标题名          [当前赛季标签]              │  │  │
│  │  │   --fs-body 600    badge                      │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │                                                    │  │
│  │  ┌─ 图表区域 ───────────────────────────────────┐  │  │
│  │  │  <v-chart autoresize />                       │  │  │
│  │  │  height: 由组件 props 指定                    │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ 控制栏 (可选) ──┐ ┌─ 统计卡片行 (可选) ─────────┐   │
│  │ 同卡片样式       │ │ flex row, gap: 12px         │   │
│  │ padding: 14px 20px│ │ 每卡片 flex:1, min-width:140px│  │
│  └─────────────────┘ └─────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  底部提示 (可选)                                   │  │
│  │  text-align: center, --fs-caption, --text-secondary│  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 7.2 两栏布局变体

用于 Hexbin 双半场对比或球员 A vs B 对比：

```
┌──────────────────────────────────────────────────────────┐
│  ┌─── 左栏 (50%) ───┐  ┌─── 右栏 (50%) ───┐            │
│  │  选择器行         │  │  选择器行         │            │
│  │  [球员A v] [赛季v]│  │  [球员B v] [赛季v]│            │
│  ├───────────────────┤  ├───────────────────┤            │
│  │                   │  │                   │            │
│  │   图表 A          │  │   图表 B          │            │
│  │                   │  │                   │            │
│  └───────────────────┘  └───────────────────┘            │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  共享控件 / 图例 (置中)                            │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 8. CSS 变量定义

将以下变量放在全局 CSS 中（`App.vue` 的 `<style>` 或独立的 `variables.css`），所有组件通过 `var(--xxx)` 引用：

```css
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
  --duration-play:    500ms;  /* KDE 播放帧间隔基准 */

  /* ===== 阴影 ===== */
  --shadow-card:  0 1px 3px rgba(0,0,0,0.3);
  --shadow-float: 0 4px 12px rgba(0,0,0,0.4);
}
```

### 8.1 组件内使用示例

```css
/* 组件 scoped style 中引用全局变量 */
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 14px 16px;
  transition: border-color var(--duration-fast) var(--ease-out);
}
.stat-card:hover {
  border-color: var(--border-hover);
}
.stat-value {
  font-size: var(--fs-stat);
  font-weight: 800;
  color: var(--text-primary);
  line-height: var(--lh-compact);
}
.stat-value.rim { color: var(--semantic-rim); }
.stat-delta.up { color: var(--semantic-made); }
.stat-delta.down { color: var(--semantic-missed); }
```

---

## 9. 核验清单

每个模块完成开发后，按此清单逐项检查视觉一致性。

### 9.1 色板

- [ ] 所有背景色来自 `--bg-*` 变量，无硬编码色值
- [ ] 投篮命中/未中全系统统一使用 `--semantic-made` / `--semantic-missed`
- [ ] 三分相关全部使用 `--semantic-three`，两分使用 `--semantic-two`
- [ ] 图表网格线/轴线颜色一致（`--chart-grid` / `--chart-axis`）
- [ ] 数据色阶（命中率）在各模块中含义相同

### 9.2 字体

- [ ] 全局 font-family 已设置为 `--font-stack`
- [ ] 标题使用 `--fs-title` 或 `--fs-hero`，无自行设定字号
- [ ] 统计数字使用 `--fs-stat`（30px, 800 weight）
- [ ] tooltip 字号为 13px，图例为 12px，轴标签为 11px
- [ ] 中文和英文混排正常，无字体回落导致的错位

### 9.3 图表

- [ ] 所有 ECharts 图表 backgroundColor 设为 `'transparent'`
- [ ] tooltip 背景色 `rgba(13,17,23,0.95)`，带 `backdrop-filter: blur(8px)`
- [ ] 图例位置统一为图表底部居中
- [ ] 动画时长 ≤ 400ms，缓动曲线 `cubicInOut`
- [ ] 双 Y 轴图表左右轴标签颜色与对应曲线颜色一致

### 9.4 状态

- [ ] 全页加载态显示旋转圆环 + "加载数据中..."
- [ ] 数据为空时显示空状态插画 + 说明文字 + "清除筛选"按钮
- [ ] 加载失败时显示错误提示 + "重新加载"按钮
- [ ] 按钮 hover/active/disabled 三态可区分
- [ ] 输入框 focus 态有蓝色外发光

### 9.5 布局

- [ ] 页面最小内边距 24px（上下）32px（左右）
- [ ] 卡片间距 16px，卡片内边距 18px 20px 12px
- [ ] 卡片圆角 10px，控制栏圆角 8px
- [ ] 两栏布局间距 16px，总宽 ≤ 页宽的 50% 各栏
- [ ] 页面宽度 < 1280px 时不出现横向滚动条破坏布局

### 9.6 跨模块一致性

- [ ] KDE 的 2020 赛季蓝色 = Hexbin 的三分区域蓝色 = 桑基图的三分节点蓝色（均为 `--semantic-three`）
- [ ] 所有模块的 tooltip 格式一致（标题加粗 + 圆点 + 值）
- [ ] 所有模块的加载/空/异常态 UI 相同
- [ ] 控制按钮（播放、滑块、速度切换）在三个模块中外观一致
- [ ] 深色主题无白色闪烁（所有容器背景透明或深色）
