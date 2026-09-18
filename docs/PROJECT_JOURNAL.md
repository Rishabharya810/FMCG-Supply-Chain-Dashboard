# Project Journal — How This Dashboard Was Built

A record of the build process, the problems hit along the way, and the
decisions taken — the kind of detail a reviewer or interviewer asks about
("why did you do it this way?").

## Phase 1 — Data cleaning (Power Query)

All six CSVs were loaded into Power BI through Power Query and cleaned:

| Problem | What we did |
|---|---|
| Invisible BOM characters on `dim_date.date` and `fact_orders_aggregate.order_id` headers | Renamed via double-click → Ctrl+A → retype (the invisible character would silently break relationships later) |
| Two different date formats — `fact_order_lines` uses long text ("Tuesday, March 1, 2022"), `fact_orders_aggregate` uses "01-Mar-22" | Both parsed to real Date type so time-based charts and the calendar connection work |
| `beverages` lowercase vs `Dairy`/`Food` Title Case in `dim_products.category` | First tried **Replace values** — it failed silently because the wrong column was selected (Power Query acts on the *selected* column). Fixed properly with **Transform → Format → Capitalize Each Word** |
| `%` signs in `dim_targets_orders` column names (`ontime_target%`…) | Renamed to `ontime_target` etc. — the values are already numbers (87 = 87%), the % is decoration that only makes DAX formulas ugly |
| `In Full` / `On Time` / `On Time In Full` spaces in `fact_order_lines` | Renamed to `in_full` / `on_time` / `on_time_in_full` |

## Phase 2 — Data model (star schema)

Target model: two fact tables (`fact_orders_aggregate` at order grain,
`fact_order_lines` at line grain), four dimensions, six single-direction
relationships — **no fact-to-fact joins**.

| Problem / decision | What we did and why |
|---|---|
| Power BI auto-created a fact-to-fact relationship (`fact_orders_aggregate.order_id` → `fact_order_lines.order_id`) | **Deleted.** Fact tables must never filter each other — filters flow dimension → fact only. Keeping it would create two competing filter paths (via `dim_customers` and via the fact link), producing ambiguous numbers you can't reason about |
| `dim_customers ↔ dim_targets_orders` was auto-created with **Both** cross-filter direction | Rebuilt as **One-to-many, Single direction** (customers → targets). The 1:1 auto-guess made Power BI default to Both; a dimension should be the "one" side with a one-way street. Also: the arrow must point customers → targets, or every matrix row would show the same (grand-average) target |
| The two `dim_date` links were missing entirely | Drawn manually. Auto-detection only matches identical column names, and ours differ (`date` vs `order_placement_date`) |
| `mmm_yy` ("Apr 2022") sorts alphabetically (Apr before Feb) | Added a `month_sort` number column in Power Query and set it as the sort-by column for `mmm_yy` |
| Power BI's automatic date tables | Disabled **Auto date/time** — we use our own `dim_date` |

## Phase 3 — Measures (19 DAX measures)

All KPIs are explicit DAX measures — no implicit aggregations:

- **KPIs:** Total Orders, Total Order Lines, On Time %, In Full %, OTIF %,
  Line Fill Rate %, Volume Fill Rate %
- **Targets:** the three per-customer target averages (`÷ 100` to convert
  87 → 0.87)
- **Gaps:** `(Actual − Target) × 100` in percentage points
- **Conditional colors:** three SWITCH measures — green `#63BE7B` at/above
  target, yellow `#FFEB84` within 10 pts, orange `#FDAE61` within 25 pts,
  red `#F8696B` beyond — wired into the matrix cells via
  "Conditional formatting → Field value"
- **Metric switcher:** a disconnected `Metrics` table (OT / IF / OTIF / LIFR /
  VOFR) with `Selected Metric Value` and `Selected Metric Target` router
  measures, plus a dynamic `Chart Title` measure that shows the current metric
  and drill level

## Phase 4 — Dashboard page build

The original one-page build, in order: KPI cards (actual vs target), the
customer × metric matrix with gap-colored cells, the city matrix, the trend
line chart with month → week → day drill, the metric switcher, and the product
table.

| Problem | What we did |
|---|---|
| Clicking a KPI card cross-filtered and "broke" the drill on the chart (the drill-down gremlin) | Used **Format → Edit interactions** to set the KPI cards and the customer matrix to "None" — the permanent cure |
| The sparkline setting was hard to find | It lives on the value field's dropdown → **Add a sparkline** (in the table's format settings), not on the main Format pane |
| Verifying numbers the dashboard shows | Exported chart/table data to CSV and compared against hand-computed values from the raw data |

## Phase 5 — Multi-page restructure

The single page became five, each with one job:

1. **Overview** — executive readout, all five KPIs vs targets, monthly trend
2. **Customers** — account matrix + city benchmark watchlist
3. **Trends** — the monthly OTIF vs target signal with the metric switcher
4. **Products** — LIFR & VOFR by product with sparklines
5. **Info** — metric definitions, data model notes, key insights

Visuals were migrated between pages with copy-paste (Ctrl+C on the source
page → Ctrl+V on the target page), then the originals were deleted.

**Final decision — the original Dashboard page was removed.** After the split,
every element on it was already covered elsewhere (KPI cards and city table on
Overview, customer matrix on Customers, metric switcher and drillable trend on
Trends, product table on Products), so keeping it meant a page that was ~95%
duplicate. The only unique element — the three gap cards (OT −27.1, IF −23.7,
OTIF −36.9 pts) — was moved to the Overview page, and the page itself was
deleted. Deleting a page removes only its visuals; all tables and measures are
untouched.

## Final verified numbers

OT% 59.0 · IF% 52.8 · OTIF% 29.0 · LIFR 66.0 · VOFR 96.6 · targets
86.1 / 76.5 / 65.9 · gaps −27.1 / −23.7 / −36.9 pts · 0 of 35 customers on
target · data window 01-Mar-2022 to 31-Aug-2022.