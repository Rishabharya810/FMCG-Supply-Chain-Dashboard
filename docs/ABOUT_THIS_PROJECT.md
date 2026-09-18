# About This Project

**AtliQ Mart — Supply Chain Service-Level Dashboard**

Codebasics Resume Project Challenge **#2** (AtliQ Mart, FMCG domain). Built in
Power BI Desktop.

## The business problem

AtliQ Mart is an FMCG manufacturer in Gujarat, India, supplying retail chains
across **Surat, Ahmedabad, and Vadodara**, with plans to expand into other metros
and Tier-1 cities. Several key customers declined to renew their annual supply
contracts, citing late and incomplete deliveries. Leadership needed a **daily
service-level tracking dashboard** to monitor on-time (OT%), in-full (IF%),
on-time-in-full (OTIF%), line fill rate (LIFR), and volume fill rate (VOFR)
performance for every customer against the negotiated targets — before expanding
to new cities.

## The dashboard

Five pages, one story:

- **Overview** — executive summary: all five KPIs against targets, city split,
  and the monthly OTIF trend.
- **Customers** — account-level matrix (OT / IF / OTIF / LIFR / VOFR) and a
  watchlist of the lowest-OTIF accounts.
- **Trends** — monthly OTIF vs target with a metric switcher and drill from
  months down to days.
- **Products** — LIFR and VOFR by product with date sparklines, filterable by
  category.
- **Definitions & Data Model** — metric definitions, star-schema documentation,
  and the key insights.

## Data

Six CSVs provided with the challenge (also included in `data/`):

| Table | Rows | Role |
|---|---|---|
| `fact_order_lines` | 57,096 | Fact — one row per order line |
| `fact_orders_aggregate` | 31,729 | Fact — one row per order (OT/IF/OTIF flags) |
| `dim_customers` | 35 | Dimension — retail customers (chain + city rows) |
| `dim_products` | 18 | Dimension — products and categories |
| `dim_date` | 183 | Dimension — daily calendar, Mar–Aug 2022 |
| `dim_targets_orders` | 35 | Dimension — per-customer OT/IF/OTIF targets |

Data window: **01-Mar-2022 to 31-Aug-2022**. Every figure in the dashboard was
verified against the raw data during the build (chart exports checked by hand).

## Verified headline numbers

| KPI | Actual | Overall target |
|---|---|---|
| OT% (On-Time) | **59.0%** | 86.1% |
| IF% (In-Full) | **52.8%** | 76.5% |
| OTIF% (On-Time In-Full) | **29.0%** | 65.9% |
| LIFR (Line Fill Rate) | **66.0%** | — (no target in source data) |
| VOFR (Volume Fill Rate) | **96.6%** | — (no target in source data) |

**0 of 35 customers** meet their OTIF target.

## Tech stack

Power BI Desktop (data modeling, DAX, Power Query) · Python/pandas (verification)

## Author

**Rishab Arya** — Data Analyst | M.Tech Data Science candidate
LinkedIn: [linkedin.com/in/rishab-arya-4a84481b1](https://www.linkedin.com/in/rishab-arya-4a84481b1)