---
name: nba-court-dimensions
description: NBA official half-court dimensions in feet and viewBox units for SVG rendering
metadata:
  type: reference
---

# NBA Half-Court Dimensions (Verified)

## Real-world distances (NBA Rule Book)

| Feature | Distance | From |
|---|---|---|
| Full court | 94 ft × 50 ft | — |
| Half court (baseline → midcourt) | 47 ft | baseline |
| Basket center from baseline | 5.25 ft (63") | baseline |
| Basket center from midcourt | **41.75 ft** | midcourt line |
| 3pt arc radius | 23.75 ft (23'9") | basket center |
| 3pt arc side straight | 3 ft inside sideline | sideline |
| Key (paint): width | 16 ft | centered on basket |
| Key (paint): depth | 19 ft | baseline |
| FT line | 19 ft from baseline | baseline (15 ft from backboard face) |
| FT circle radius | 6 ft | centered on FT line midpoint |
| Restricted arc radius | 4 ft | basket center |
| Sideline width | 50 ft | — |
| 3pt corner depth | 3 ft | sideline |

## Data coordinate system (Python preprocessing)

- 1 data unit = **0.1 ft** (tenths of a foot)
- Basket at origin `(0, 0)`
- X: -250 (left) to 250 (right) = 50 ft total
- Y: 0 (basket) to 470 (47 ft out = just past midcourt at 41.75 ft)
- Data Y max = 470 ≈ 47 ft from basket → 52.25 ft from baseline (past half-court line)
- hex_radius = 15 data units = 1.5 ft

## Classic "basket-at-bottom" viewBox: `"0 0 600 600"`

Scale: **1 ft = 10 px**. viewBox is square with 50 px margins around the court area.

| Element | viewBox coords | Real-world |
|---|---|---|
| Basket center | `(300, 500)` | origin |
| Baseline | `y = 552.5` (x: 50→550) | 5.25 ft below basket |
| Midcourt line | `y = 82.5` (x: 50→550) | 41.75 ft above basket (47 ft from baseline) |
| Sidelines | `x = 50, 550` (y: 82.5→552.5) | 25 ft each side of center |
| 3pt arc center | `(300, 500)`, R = 237.5 | 23.75 ft |
| 3pt straight (x) | `x = 80, 520` | 3 ft inside sideline |
| 3pt arc/straight intersection | `y ≈ 410.5` (at x=80,520) | solved from (237.5² - 220²) |
| Paint/Key | `x: 220→380, y: 362.5→552.5` | 16 ft × 19 ft from baseline |
| FT line | `y = 362.5` | 19 ft from baseline |
| FT half-circle | center `(300, 362.5)`, R = 60 | 6 ft above FT line |
| Restricted arc | center `(300, 500)`, R = 40 | 4 ft toward baseline |

## Data → ViewBox Transform

**1:1 mapping** — both data and viewBox use 10 units/ft:
- `viewX = 300 + dataX`
- `viewY = 500 - dataY`

Verification:
- data `(0,0)` → viewBox `(300,500)` = basket position ✓
- data `(-250, 0)` → viewBox `(50, 500)` = left sideline at basket level ✓
- data `(0, 417.5)` → viewBox `(300, 82.5)` = midcourt ✓
- data max Y=468 → viewBox `(300, 32)` = ~46.8 ft out, past midcourt ✓

## Hex properties

- Flat-top hexagons (θ=0° flat face up, matches Python output)
- Size range: R_min = 1.5, R_max = 15 (viewBox units)
- Sorted by radius descending (biggest hexes render first = appear "under" smaller)
