/**
 * FG% → color scale for hexbin classic view.
 *
 * User requirement: high FG% → deeper red (高命中率=深红),
 *                    low FG%  → pale orange (低命中率=淡橙, low sat).
 *
 * Sequential reds palette (5 stops):
 *   0%   → #fbe3c8  (very pale peach, nearly invisible)
 *   25%  → #f4a460  (light sandy orange)
 *   40%  → #e8733a  (orange-red)
 *   55%  → #c9381a  (deep orange-red)
 *   70%  → #9e1206  (dark saturated red)
 *   100% → #7a0b02  (deepest red)
 */

const STOPS: [number, string][] = [
  [0.0, '#fbe3c8'],
  [0.25, '#f4a460'],
  [0.40, '#e8733a'],
  [0.55, '#c9381a'],
  [0.70, '#9e1206'],
  [1.00, '#7a0b02'],
];

export function fgPctColorClassic(fgPct: number): string {
  if (fgPct <= STOPS[0][0]) return STOPS[0][1];
  if (fgPct >= STOPS[STOPS.length - 1][0]) return STOPS[STOPS.length - 1][1];

  for (let i = 0; i < STOPS.length - 1; i++) {
    const [t0, c0] = STOPS[i];
    const [t1, c1] = STOPS[i + 1];
    if (fgPct >= t0 && fgPct <= t1) {
      return interpolateHex(c0, c1, (fgPct - t0) / (t1 - t0));
    }
  }
  return STOPS[0][1];
}

function interpolateHex(c1: string, c2: string, t: number): string {
  const r1 = parseInt(c1.slice(1, 3), 16);
  const g1 = parseInt(c1.slice(3, 5), 16);
  const b1 = parseInt(c1.slice(5, 7), 16);
  const r2 = parseInt(c2.slice(1, 3), 16);
  const g2 = parseInt(c2.slice(3, 5), 16);
  const b2 = parseInt(c2.slice(5, 7), 16);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return `#${hex(r)}${hex(g)}${hex(b)}`;
}

function hex(v: number): string {
  return v.toString(16).padStart(2, '0');
}

export const FG_PCT_STOPS_CLASSIC = [0, 0.25, 0.4, 0.55, 0.7, 1.0];
export const FG_PCT_COLORS_CLASSIC = ['#fbe3c8', '#f4a460', '#e8733a', '#c9381a', '#9e1206', '#7a0b02'];
