# DAX Measure Reference

All measures live in the `Measures table` of the semantic model.

## Base aggregations

| Measure | Formula |
|---|---|
| `Total Orders` | `COUNTROWS(fact_orders_aggregate)` |
| `Total Order Lines` | `COUNTROWS(fact_order_lines)` |

## Service-level KPIs

| Measure | Grain | Formula |
|---|---|---|
| `On Time %` | Order | `DIVIDE(SUM(fact_orders_aggregate[on_time]), [Total Orders])` |
| `In Full %` | Order | `DIVIDE(SUM(fact_orders_aggregate[in_full]), [Total Orders])` |
| `OTIF %` | Order | `DIVIDE(SUM(fact_orders_aggregate[otif]), [Total Orders])` |
| `Line Fill Rate %` | Line | `DIVIDE(SUM(fact_order_lines[in_full]), [Total Order Lines])` |
| `Volume Fill Rate %` | Line | `DIVIDE(SUM(fact_order_lines[delivery_qty]), SUM(fact_order_lines[order_qty]))` |

## Targets (per-customer, averaged)

| Measure | Formula |
|---|---|
| `On Time Target %` | `DIVIDE(AVERAGE(dim_targets_orders[ontime_target]), 100)` |
| `In Full Target %` | `DIVIDE(AVERAGE(dim_targets_orders[infull_target]), 100)` |
| `OTIF Target %` | `DIVIDE(AVERAGE(dim_targets_orders[otif_target]), 100)` |

## Gap vs target (percentage points) and conditional colors

| Measure | Formula |
|---|---|
| `OT Gap` | `([On Time %] - [On Time Target %]) * 100` |
| `IF Gap` | `([In Full %] - [In Full Target %]) * 100` |
| `OTIF Gap` | `([OTIF %] - [OTIF Target %]) * 100` |
| `OT Gap Color` / `IF Gap Color` / `OTIF Gap Color` | `SWITCH` on gap points: ≥ 0 green `#63BE7B`, ≥ −10 yellow `#FFEB84`, ≥ −25 orange `#FDAE61`, else red `#F8696B` |

## Metric switcher (disconnected `Metrics` table)

| Measure | Purpose |
|---|---|
| `Selected Metric Value` | `SWITCH(SELECTEDVALUE(Metrics[Metric]), "OT %", [On Time %], "IF %", [In Full %], "OTIF %", [OTIF %], "LIFR %", [Line Fill Rate %], "VOFR %", [Volume Fill Rate %])` |
| `Selected Metric Target` | Same pattern for OT / IF / OTIF targets (blank for LIFR/VOFR — no targets in source data) |
| `Chart Title` | Dynamic title with the selected metric and current drill level (daily / weekly / monthly) |

## Verified values

OT% 59.0 · IF% 52.8 · OTIF% 29.0 · LIFR 66.0 · VOFR 96.6 · targets 86.1 / 76.5 / 65.9
· gaps −27.1 / −23.7 / −36.9 points · 0 of 35 customers on target.