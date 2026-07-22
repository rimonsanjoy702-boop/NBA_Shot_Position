<template>
  <div class="three-chart-wrap">
    <!-- ============================================================
         图表1 — 场均三分出手数 3PA
         ============================================================ -->
    <div class="chart-panel">
      <h3 class="chart-title">场均三分出手 3PA</h3>
      <div ref="chart3PaDom" class="chart-svg"></div>
    </div>

    <!-- ============================================================
         图表2 — 三分出手占总出手比 3PAr
         ============================================================ -->
    <div class="chart-panel">
      <h3 class="chart-title">三分出手占比 3PAr</h3>
      <div ref="chart3ParDom" class="chart-svg"></div>
    </div>

    <!-- ============================================================
         图表3 — 常规赛胜率 WinPct
         ============================================================ -->
    <div class="chart-panel">
      <h3 class="chart-title">常规赛胜率 WinPct</h3>
      <div ref="chartWinDom" class="chart-svg"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from "vue";
import * as d3 from "d3";
import type { AggDataMap, GroupAggEntry } from "../store";

const props = defineProps<{
  aggData: AggDataMap;
  seasons: string[];
  showMid: boolean;
}>();

const chart3PaDom = ref<HTMLDivElement | null>(null);
const chart3ParDom = ref<HTMLDivElement | null>(null);
const chartWinDom = ref<HTMLDivElement | null>(null);

// ==========================================================================
// Constants
// ==========================================================================

const SVG_W = 1880;
const SVG_H = 420;
const MARGIN = { top: 24, right: 40, bottom: 48, left: 60 };
const PLOT_W = SVG_W - MARGIN.left - MARGIN.right;
const PLOT_H = SVG_H - MARGIN.top - MARGIN.bottom;

const GROUP_CONFIG: Record<string, { stroke: string; lw: number; dash: string | null; label: string; zIdx: number }> = {
  leader:  { stroke: "#e63946", lw: 3, dash: null,      label: "先行者", zIdx: 3 },
  laggard: { stroke: "#457b9d", lw: 2, dash: "6,3",      label: "落后者", zIdx: 2 },
  mid:     { stroke: "#f4a261", lw: 2, dash: "2,4",      label: "过渡组", zIdx: 1 },
};

const VERTICAL_MARKS = [
  { season: "2014-15", label: "2014-15 先行者窗口终点",  color: "#e63946" },
  { season: "2018-19", label: "2018-19 落后者转型起点",  color: "#457b9d" },
];

const Y_RANGES: Record<string, [number, number]> = {
  "3pa":  [0, 45],
  "3par": [0, 0.55],
  "win":  [0, 0.75],
};

// ==========================================================================
// Shared helpers
// ==========================================================================

interface PlotContext {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>;
  xScale: d3.ScalePoint<string>;
  yScale: d3.ScaleLinear<number, number>;
  g: d3.Selection<SVGGElement, unknown, null, undefined>;
}

function makeSvg(
  container: HTMLDivElement,
  yDomain: [number, number],
  seasons: string[],
): PlotContext {
  // Clear
  container.innerHTML = "";

  const svg = d3.select(container)
    .append("svg")
    .attr("viewBox", `0 0 ${SVG_W} ${SVG_H}`)
    .attr("width", "100%")
    .attr("height", "auto")
    .attr("preserveAspectRatio", "xMidYMid meet");

  // Background
  svg.append("rect")
    .attr("x", 0).attr("y", 0)
    .attr("width", SVG_W).attr("height", SVG_H)
    .attr("fill", "var(--bg-root, #0d1117)");

  const g = svg.append("g")
    .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

  const xScale = d3.scalePoint<string>()
    .domain(seasons)
    .range([0, PLOT_W])
    .padding(0.5);

  const yScale = d3.scaleLinear()
    .domain(yDomain)
    .range([PLOT_H, 0])
    .nice();

  // Grid lines
  g.append("g")
    .attr("class", "grid")
    .call(
      d3.axisLeft(yScale)
        .ticks(6)
        .tickSize(-PLOT_W)
        .tickFormat("" as any)
    )
    .selectAll("line")
    .attr("stroke", "var(--chart-grid, rgba(255,255,255,0.06))")
    .attr("stroke-dasharray", "4,4");

  // Y axis
  g.append("g")
    .attr("class", "y-axis")
    .call(d3.axisLeft(yScale).ticks(6))
    .selectAll("text")
    .attr("fill", "var(--text-secondary, #8b949e)")
    .attr("font-size", "13");

  g.selectAll(".y-axis .domain, .y-axis .tick line")
    .attr("stroke", "var(--chart-axis, rgba(255,255,255,0.15))");

  // X axis
  const xAxis = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${PLOT_H})`)
    .call(
      d3.axisBottom(xScale)
        .tickValues(xScale.domain().filter((_, i) => i % 1 === 0))
    );

  xAxis.selectAll("text")
    .attr("fill", "var(--text-secondary, #8b949e)")
    .attr("font-size", "12")
    .attr("transform", "rotate(-45)")
    .style("text-anchor", "end");

  xAxis.selectAll(".domain, .tick line")
    .attr("stroke", "var(--chart-axis, rgba(255,255,255,0.15))");

  return { svg, xScale, yScale, g };
}

function getValue(d: GroupAggEntry | undefined, key: string): number | null {
  if (!d) return null;
  const v = (d as any)[key];
  return typeof v === "number" ? v : null;
}

// ==========================================================================
// Multi-line tooltip
// ==========================================================================

function addTooltip(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  xScale: d3.ScalePoint<string>,
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  seasons: string[],
  aggData: AggDataMap,
  showMid: boolean,
  metric: string,
) {
  // Transparent overlay for mouse tracking
  const overlay = g.append("rect")
    .attr("width", PLOT_W)
    .attr("height", PLOT_H)
    .attr("fill", "transparent")
    .style("pointer-events", "all");

  const tooltip = svg.append("g")
    .attr("class", "tooltip")
    .style("visibility", "hidden")
    .style("pointer-events", "none");

  const tooltipBg = tooltip.append("rect")
    .attr("rx", 6)
    .attr("ry", 6)
    .attr("fill", "var(--bg-overlay, rgba(0,0,0,0.85))")
    .attr("stroke", "var(--border-card, rgba(255,255,255,0.12))")
    .attr("stroke-width", 1);

  const tooltipText = tooltip.append("text")
    .attr("x", 12)
    .attr("y", 22)
    .attr("fill", "var(--text-primary, #e6edf3)")
    .attr("font-size", "13")
    .style("white-space", "pre");

  const tooltipLine = g.append("line")
    .attr("class", "tooltip-line")
    .attr("y1", 0).attr("y2", PLOT_H)
    .attr("stroke", "var(--text-tertiary, #5c6670)")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "4,4")
    .style("visibility", "hidden");

  const groupsShown = showMid
    ? (["leader", "laggard", "mid"] as const)
    : (["leader", "laggard"] as const);

  overlay.on("mousemove", (event: MouseEvent) => {
    const [mx] = d3.pointer(event, g.node());
    // Find nearest season
    let bestIdx = 0;
    let bestDist = Infinity;
    seasons.forEach((s, i) => {
      const sx = xScale(s)!;
      const d = Math.abs(sx - mx);
      if (d < bestDist) { bestDist = d; bestIdx = i; }
    });

    const snapX = xScale(seasons[bestIdx])!;
    const season = seasons[bestIdx];
    const entry = aggData[season];

    // Build tooltip lines
    const lines: string[] = [season]
    const noShotData = season >= "2020-21"
    if (noShotData && metric !== "avg_win_pct") {
      lines.push("(无投篮数据)")
    }
    groupsShown.forEach((gtype) => {
      const cfg = GROUP_CONFIG[gtype];
      const grp = entry?.[gtype];
      if (!grp) return;
      const val = getValue(grp, metric);
      if (val == null) {
        if (metric !== "avg_win_pct" && noShotData) {
          // shot data not available for this season
        }
        return;
      }
      let valStr: string
      if (metric === "avg_win_pct") {
        valStr = (val * 100).toFixed(1) + "%"
      } else if (metric === "avg_3par") {
        valStr = val.toFixed(3)
      } else {
        valStr = val.toFixed(1)
      }
      lines.push(`${cfg.label}: ${valStr}  (${grp.team_cnt}队)`)
    });

    const tspan = tooltipText
      .selectAll<SVGTSpanElement, string>("tspan")
      .data(lines);

    tspan.join("tspan")
      .attr("x", 12)
      .attr("dy", (_d: string, i: number) => i === 0 ? 0 : "1.35em")
      .text((d: string) => d);

    const { width: tw, height: th } = (
      tooltipText.node() as SVGTextElement
    ).getBBox();

    tooltipBg
      .attr("width", tw + 24)
      .attr("height", th + 28);

    const tx = snapX + 16;
    const ty = 16;
    // Flip if too far right
    const finalX = tx + tw + 24 > SVG_W ? snapX - tw - 40 : tx;

    tooltip.attr("transform", `translate(${finalX},${ty})`);
    tooltip.style("visibility", "visible");

    tooltipLine
      .attr("x1", snapX).attr("x2", snapX)
      .style("visibility", "visible");
  });

  overlay.on("mouseleave", () => {
    tooltip.style("visibility", "hidden");
    tooltipLine.style("visibility", "hidden");
  });
}

// ==========================================================================
// Draw a single chart
// ==========================================================================

function drawChart(
  container: HTMLDivElement,
  seasons: string[],
  aggData: AggDataMap,
  showMid: boolean,
  metric: "avg_3pa" | "avg_3par" | "avg_win_pct",
  yRange: [number, number],
) {
  const ctx = makeSvg(container, yRange, seasons);
  const { svg, xScale, yScale, g } = ctx;

  const groupsShown = showMid
    ? (["leader", "laggard", "mid"] as const)
    : (["leader", "laggard"] as const);

  // Line generator
  const lineGen = d3.line<[number, number]>()
    .x((d) => d[0])
    .y((d) => d[1]);

  // Draw one curve per group
  groupsShown.forEach((gtype) => {
    const cfg = GROUP_CONFIG[gtype];

    const points: [number, number][] = [];
    seasons.forEach((s) => {
      const entry = aggData[s];
      const grp = entry?.[gtype];
      const v = getValue(grp, metric);
      if (v != null) {
        points.push([xScale(s)!, yScale(v)]);
      }
    });

    if (points.length === 0) return;

    g.append("path")
      .datum(points)
      .attr("d", lineGen)
      .attr("fill", "none")
      .attr("stroke", cfg.stroke)
      .attr("stroke-width", cfg.lw)
      .attr("stroke-dasharray", cfg.dash ?? "none");

    // Small dot markers
    g.selectAll(`.dot-${gtype}`)
      .data(points)
      .join("circle")
      .attr("cx", (d) => d[0])
      .attr("cy", (d) => d[1])
      .attr("r", gtype === "leader" ? 4 : 3)
      .attr("fill", cfg.stroke);
  });

  // ---- Vertical reference lines ----
  VERTICAL_MARKS.forEach((vm) => {
    const vx = xScale(vm.season);
    if (vx == null) return;

    // Line
    g.append("line")
      .attr("x1", vx).attr("x2", vx)
      .attr("y1", 0).attr("y2", PLOT_H)
      .attr("stroke", vm.color)
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "6,4")
      .attr("opacity", 0.7);

    // Label at top
    g.append("text")
      .attr("x", vx + 6)
      .attr("y", 14)
      .attr("fill", vm.color)
      .attr("font-size", "11")
      .text(vm.label);
  });

  // ---- Data-cutoff line for 3PA / 3PAr charts (2020 onwards = win% only) ----
  if (metric !== "avg_win_pct") {
    const x20 = xScale("2019-20");
    if (x20 != null) {
      g.append("line")
        .attr("x1", x20 + 8).attr("x2", x20 + 8)
        .attr("y1", 0).attr("y2", PLOT_H)
        .attr("stroke", "var(--text-tertiary, #5c6670)")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "2,6");

      g.append("text")
        .attr("x", x20 + 14)
        .attr("y", PLOT_H - 8)
        .attr("fill", "var(--text-tertiary, #5c6670)")
        .attr("font-size", "10")
        .text("投篮数据截止");
    }
  }

  // ---- Region highlights ----
  // 2014-15 → 2018-19 window
  const x15 = xScale("2014-15");
  const x19 = xScale("2018-19");
  if (x15 != null && x19 != null) {
    g.insert("rect", ":first-child")
      .attr("x", x15)
      .attr("y", 0)
      .attr("width", x19 - x15)
      .attr("height", PLOT_H)
      .attr("fill", "rgba(244,162,97,0.06)");
  }

  // Post-2018-19 window
  if (x19 != null) {
    g.insert("rect", ":first-child")
      .attr("x", x19)
      .attr("y", 0)
      .attr("width", PLOT_W - x19)
      .attr("height", PLOT_H)
      .attr("fill", "rgba(69,123,157,0.05)");
  }

  // Tooltip
  addTooltip(svg, xScale, g, seasons, aggData, showMid, metric);
}

// ==========================================================================
// Watcher — redraw all 3 charts when data or showMid changes
// ==========================================================================

watch(
  () => [props.aggData, props.seasons, props.showMid] as const,
  async ([aggData, seasons, showMid]) => {
    if (!aggData || Object.keys(aggData).length === 0) return;
    await nextTick();

    if (chart3PaDom.value) {
      drawChart(chart3PaDom.value, seasons, aggData, showMid, "avg_3pa", Y_RANGES["3pa"]);
    }
    if (chart3ParDom.value) {
      drawChart(chart3ParDom.value, seasons, aggData, showMid, "avg_3par", Y_RANGES["3par"]);
    }
    if (chartWinDom.value) {
      drawChart(chartWinDom.value, seasons, aggData, showMid, "avg_win_pct", Y_RANGES["win"]);
    }
  },
  { immediate: false },
);

// Initial draw
onMounted(async () => {
  await nextTick();
  const { aggData, seasons, showMid } = props;
  if (!aggData || Object.keys(aggData).length === 0) return;

  if (chart3PaDom.value) {
    drawChart(chart3PaDom.value, seasons, aggData, showMid, "avg_3pa", Y_RANGES["3pa"]);
  }
  if (chart3ParDom.value) {
    drawChart(chart3ParDom.value, seasons, aggData, showMid, "avg_3par", Y_RANGES["3par"]);
  }
  if (chartWinDom.value) {
    drawChart(chartWinDom.value, seasons, aggData, showMid, "avg_win_pct", Y_RANGES["win"]);
  }
});

onUnmounted(() => {
  // D3 selections are scoped to container DOM which Vue removes,
  // but clear any remaining listeners
  [chart3PaDom, chart3ParDom, chartWinDom].forEach((d) => {
    if (d.value) d.value.innerHTML = "";
  });
});
</script>

<style scoped>
.three-chart-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.chart-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: var(--space-md) var(--space-md) var(--space-sm);
}

.chart-title {
  margin: 0 0 var(--space-sm) var(--space-sm);
  font-size: var(--fs-subtitle);
  font-weight: 600;
  color: var(--text-primary);
}

.chart-svg {
  width: 100%;
  overflow: hidden;
}

.chart-svg :deep(svg) {
  display: block;
  width: 100%;
  height: auto;
}
</style>
