# DAX Measure Reference

All 19 measures live in the `Measures table` of the semantic model, plus the
disconnected `Metrics` table that powers the metric switcher. Every number on
the dashboard comes from these — no implicit aggregations are used anywhere.

## Base aggregations

```dax
Total Orders      = COUNTROWS ( fact_orders_aggregate )
Total Order Lines = COUNTROWS ( fact_order_lines )
```

## Service-level KPIs

`DIVIDE` is used instead of `/` everywhere — it returns BLANK (not an error)
when the denominator is zero, e.g. a filtered view with no orders.
The 0/1 flag columns act as counters: `SUM` of the flags = count of "yes".

```dax
On Time % = DIVIDE ( SUM ( fact_orders_aggregate[on_time] ), [Total Orders] )

In Full % = DIVIDE ( SUM ( fact_orders_aggregate[in_full] ), [Total Orders] )

OTIF %    = DIVIDE ( SUM ( fact_orders_aggregate[otif] ), [Total Orders] )

Line Fill Rate % =
    DIVIDE ( SUM ( fact_order_lines[in_full] ), [Total Order Lines] )

Volume Fill Rate % =
    DIVIDE (
        SUM ( fact_order_lines[delivery_qty] ),
        SUM ( fact_order_lines[order_qty] )
    )
```

| Measure | Grain | Verified value |
|---|---|---|
| On Time % | Order | 59.0% |
| In Full % | Order | 52.8% |
| OTIF % | Order | 29.0% |
| Line Fill Rate % | Line | 66.0% |
| Volume Fill Rate % | Line | 96.6% |

## Targets (per-customer, averaged)

Targets are stored as whole numbers (87 = 87%), so the average is divided by 100.

```dax
On Time Target % = DIVIDE ( AVERAGE ( dim_targets_orders[ontime_target] ), 100 )

In Full Target % = DIVIDE ( AVERAGE ( dim_targets_orders[infull_target] ), 100 )

OTIF Target %    = DIVIDE ( AVERAGE ( dim_targets_orders[otif_target] ), 100 )
```

| Measure | Verified value |
|---|---|
| On Time Target % | 86.1% |
| In Full Target % | 76.5% |
| OTIF Target % | 65.9% |

## Gap vs target (percentage points)

Actual and target are both 0–1 fractions, so the difference is multiplied by
100 to express the gap in percentage points.

```dax
OT Gap   = ( [On Time %] - [On Time Target %] ) * 100

IF Gap   = ( [In Full %] - [In Full Target %] ) * 100

OTIF Gap = ( [OTIF %] - [OTIF Target %] ) * 100
```

| Measure | Verified value |
|---|---|
| OT Gap | −27.1 pts |
| IF Gap | −23.7 pts |
| OTIF Gap | −36.9 pts |

## Conditional colors (gap → traffic light)

A `SWITCH ( TRUE (), … )` ladder — the standard DAX pattern for tiered
thresholds. These measures are wired into the matrix cells via
*Conditional formatting → Field value*.

```dax
OT Gap Color =
VAR GapPoints = [OT Gap]
RETURN
    SWITCH (
        TRUE (),
        GapPoints >= 0,   "#63BE7B",   -- green  (at/above target)
        GapPoints >= -10, "#FFEB84",   -- yellow (within 10 pts)
        GapPoints >= -25, "#FDAE61",   -- orange (within 25 pts)
        "#F8696B"                      -- red    (beyond 25 pts)
    )
```

`IF Gap Color` and `OTIF Gap Color` are identical with `[IF Gap]` / `[OTIF Gap]`.

## Metric switcher (disconnected `Metrics` table)

The `Metrics` table holds one column, `Metric`, with the five values
`OT %`, `IF %`, `OTIF %`, `LIFR %`, `VOFR %`. It has **no relationships** — it
exists only to feed the slicer. `SELECTEDVALUE` reads the user's selection and
`SWITCH` routes it to the right measure.

```dax
Selected Metric Value =
SWITCH (
    SELECTEDVALUE ( Metrics[Metric] ),
    "OT %",   [On Time %],
    "IF %",   [In Full %],
    "OTIF %", [OTIF %],
    "LIFR %", [Line Fill Rate %],
    "VOFR %", [Volume Fill Rate %],
    BLANK ()
)

Selected Metric Target =
SWITCH (
    SELECTEDVALUE ( Metrics[Metric] ),
    "OT %",   [On Time Target %],
    "IF %",   [In Full Target %],
    "OTIF %", [OTIF Target %],
    BLANK ()       -- LIFR/VOFR have no targets in the source data
)
```

## Dynamic chart title

Shows the selected metric and the current drill level. `ISFILTERED` (not
`ISINSCOPE`) is used because it reliably detects the active drill level even
from the title's evaluation context.

```dax
Chart Title =
VAR MetricName = SELECTEDVALUE ( Metrics[Metric] )
VAR DrillLevel =
    SWITCH (
        TRUE (),
        ISFILTERED ( dim_date[date] ),   "Daily",
        ISFILTERED ( dim_date[week_no] ), "Weekly",
        ISFILTERED ( dim_date[mmm_yy] ),  "Monthly",
        ""
    )
RETURN
    IF (
        NOT HASONEVALUE ( Metrics[Metric] ),
        "Select a Metric",
        IF (
            DrillLevel = "",
            MetricName & " vs Target",
            MetricName & " vs Target — " & DrillLevel
        )
    )
```

## DAX habits used throughout

- **`DIVIDE` over `/`** — safe divide-by-zero.
- **`SUM` on 0/1 flags** — counts the "yes" rows.
- **`SWITCH ( TRUE (), … )` ladder** — tiered thresholds in one measure.
- **`VAR … RETURN`** — compute once, reuse.
- **`SELECTEDVALUE` + disconnected table** — slicer-driven measure switching.
- **Explicit measures only** — no implicit aggregations anywhere in the report.