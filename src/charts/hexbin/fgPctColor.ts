/**
 * FG% color scale — maps field goal percentage (0-1) to colors
 * Follows NBA可视分析系统_共享视觉规范 §2.6
 */
export function fgPctColor(fgPct: number): string {
  const stops: [number, string][] = [
    [0.0, '#ff6b6b'],   // very low
    [0.3, '#f4a460'],   // low
    [0.4, '#f4d03f'],   // medium
    [0.5, '#5cdb8b'],   // high
    [0.6, '#00d2a0'],   // very high
  ];

  if (fgPct <= stops[0][0]) return stops[0][1];
  if (fgPct >= stops[stops.length - 1][0]) return stops[stops.length - 1][1];

  // Find segment and interpolate
  for (let i = 0; i < stops.length - 1; i++) {
    const [t0, c0] = stops[i];
    const [t1, c1] = stops[i + 1];
    if (fgPct >= t0 && fgPct <= t1) {
      const ratio = (fgPct - t0) / (t1 - t0);
      return interpolateColor(c0, c1, ratio);
    }
  }

  return stops[0][1];
}

/** Linear interpolation between two hex colors */
function interpolateColor(c1: string, c2: string, t: number): string {
  const r1 = parseInt(c1.slice(1, 3), 16);
  const g1 = parseInt(c1.slice(3, 5), 16);
  const b1 = parseInt(c1.slice(5, 7), 16);
  const r2 = parseInt(c2.slice(1, 3), 16);
  const g2 = parseInt(c2.slice(3, 5), 16);
  const b2 = parseInt(c2.slice(5, 7), 16);

  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

export const FG_PCT_STOPS = [0, 0.3, 0.4, 0.5, 0.6, 1.0];
export const FG_PCT_COLORS = ['#ff6b6b', '#f4a460', '#f4d03f', '#5cdb8b', '#00d2a0'];
