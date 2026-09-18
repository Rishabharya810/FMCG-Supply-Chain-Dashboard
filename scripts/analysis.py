"""
AtliQ Mart — FMCG Supply Chain Service-Level Analysis
======================================================
Computes order-fulfillment KPIs from raw operational data and exports
verified metrics, breakdowns, and charts used to build the Power BI
dashboard and the insights report.

KPI definitions (industry-standard service-level metrics)
----------------------------------------------------------
OT%   On-Time %            share of orders delivered on/before agreed date
IF%   In-Full %            share of orders delivered in full ordered qty
OTIF% On-Time In-Full %    share of orders delivered both on-time AND in-full
LIFR  Line Fill Rate       share of order LINES delivered in full
VOFR  Volume Fill Rate      delivered volume / ordered volume (across all lines)

Author: Rishab Arya
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.dirname(__file__)
CHART_DIR = os.path.join(OUT_DIR, "charts")
os.makedirs(CHART_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.dpi": 130,
    "font.size": 10,
    "axes.titleweight": "bold",
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("Loading data...")
# encoding handles the UTF-8 BOM present in several source files.
dim_cust = pd.read_csv(f"{DATA_DIR}/dim_customers.csv", encoding="utf-8-sig")
dim_date = pd.read_csv(f"{DATA_DIR}/dim_date.csv", encoding="utf-8-sig")
dim_prod = pd.read_csv(f"{DATA_DIR}/dim_products.csv", encoding="utf-8-sig")
dim_targ = pd.read_csv(f"{DATA_DIR}/dim_targets_orders.csv", encoding="utf-8-sig")
fact_lines = pd.read_csv(f"{DATA_DIR}/fact_order_lines.csv", encoding="utf-8-sig")
fact_agg = pd.read_csv(f"{DATA_DIR}/fact_orders_aggregate.csv", encoding="utf-8-sig")

print(f"  dim_customers:        {dim_cust.shape}")
print(f"  dim_date:             {dim_date.shape}")
print(f"  dim_products:         {dim_prod.shape}")
print(f"  dim_targets_orders:   {dim_targ.shape}")
print(f"  fact_order_lines:     {fact_lines.shape}")
print(f"  fact_orders_aggregate:{fact_agg.shape}")

# ---------------------------------------------------------------------------
# Clean / parse dates
# ---------------------------------------------------------------------------
print("\nParsing dates...")
# fact_orders_aggregate.order_placement_date  -> "01-Mar-22"
fact_agg["order_placement_date"] = pd.to_datetime(
    fact_agg["order_placement_date"], format="%d-%b-%y", errors="coerce"
)

# fact_order_lines dates -> "Tuesday, March 1, 2022"
date_fmt = "%A, %B %d, %Y"
fact_lines["order_placement_date"] = pd.to_datetime(
    fact_lines["order_placement_date"], format=date_fmt, errors="coerce"
)
fact_lines["agreed_delivery_date"] = pd.to_datetime(
    fact_lines["agreed_delivery_date"], format=date_fmt, errors="coerce"
)
fact_lines["actual_delivery_date"] = pd.to_datetime(
    fact_lines["actual_delivery_date"], format=date_fmt, errors="coerce"
)

# dim_date.date -> "01-Apr-22"
dim_date["date"] = pd.to_datetime(dim_date["date"], format="%d-%b-%y", errors="coerce")

# Normalize line-level flag column names to snake_case
fact_lines = fact_lines.rename(columns={
    "In Full": "in_full_line",
    "On Time": "on_time_line",
    "On Time In Full": "otif_line",
})

# Add a month key for trend analysis
fact_agg["month"] = fact_agg["order_placement_date"].dt.to_period("M")
fact_lines["month"] = fact_lines["order_placement_date"].dt.to_period("M")

# ---------------------------------------------------------------------------
# 1. Overall KPIs (order level from fact_orders_aggregate + line/volume level)
# ---------------------------------------------------------------------------
print("\n=== OVERALL KPIs ===")
total_orders = len(fact_agg)
ot_pct = fact_agg["on_time"].mean() * 100
if_pct = fact_agg["in_full"].mean() * 100
otif_pct = fact_agg["otif"].mean() * 100

total_lines = len(fact_lines)
lifr = fact_lines["in_full_line"].mean() * 100
vofr = fact_lines["delivery_qty"].sum() / fact_lines["order_qty"].sum() * 100

kpi_summary = pd.DataFrame([
    {"metric": "OT%", "description": "On-Time % (order level)",
     "value_pct": round(ot_pct, 2), "grain": "order", "records": total_orders},
    {"metric": "IF%", "description": "In-Full % (order level)",
     "value_pct": round(if_pct, 2), "grain": "order", "records": total_orders},
    {"metric": "OTIF%", "description": "On-Time In-Full % (order level)",
     "value_pct": round(otif_pct, 2), "grain": "order", "records": total_orders},
    {"metric": "LIFR", "description": "Line Fill Rate (line level)",
     "value_pct": round(lifr, 2), "grain": "line", "records": total_lines},
    {"metric": "VOFR", "description": "Volume Fill Rate (volume level)",
     "value_pct": round(vofr, 2), "grain": "volume", "records": total_lines},
])
print(kpi_summary.to_string(index=False))
kpi_summary.to_csv(f"{OUT_DIR}/kpi_summary.csv", index=False)

# ---------------------------------------------------------------------------
# 2. Per-customer actual vs target
# ---------------------------------------------------------------------------
print("\n=== PER-CUSTOMER KPIs (actual vs target) ===")
cust_kpi = fact_agg.groupby("customer_id").agg(
    orders=("order_id", "count"),
    ot_pct=("on_time", "mean"),
    if_pct=("in_full", "mean"),
    otif_pct=("otif", "mean"),
).reset_index()
cust_kpi[["ot_pct", "if_pct", "otif_pct"]] *= 100

cust_kpi = cust_kpi.merge(dim_cust, on="customer_id", how="left")
cust_kpi = cust_kpi.merge(dim_targ, on="customer_id", how="left")
cust_kpi["ot_variance"] = cust_kpi["ot_pct"] - cust_kpi["ontime_target%"]
cust_kpi["if_variance"] = cust_kpi["if_pct"] - cust_kpi["infull_target%"]
cust_kpi["otif_variance"] = cust_kpi["otif_pct"] - cust_kpi["otif_target%"]
cust_kpi["otif_meets_target"] = cust_kpi["otif_variance"] >= 0
cust_kpi = cust_kpi.sort_values("orders", ascending=False)
cust_kpi.to_csv(f"{OUT_DIR}/customer_kpis.csv", index=False)
print(cust_kpi[["customer_name", "city", "orders", "ot_pct", "if_pct",
               "otif_pct", "otif_target%", "otif_variance"]].head(12).to_string(index=False))

# ---------------------------------------------------------------------------
# 3. Per-city KPIs
# ---------------------------------------------------------------------------
print("\n=== PER-CITY KPIs ===")
city_kpi = fact_agg.merge(dim_cust, on="customer_id").groupby("city").agg(
    orders=("order_id", "count"),
    ot_pct=("on_time", "mean"),
    if_pct=("in_full", "mean"),
    otif_pct=("otif", "mean"),
).reset_index()
city_kpi[["ot_pct", "if_pct", "otif_pct"]] *= 100
city_kpi = city_kpi.sort_values("orders", ascending=False)
city_kpi.to_csv(f"{OUT_DIR}/city_kpis.csv", index=False)
print(city_kpi.to_string(index=False))

# ---------------------------------------------------------------------------
# 4. Per-product / category KPIs (line & volume level)
# ---------------------------------------------------------------------------
print("\n=== PER-CATEGORY KPIs ===")
prod_kpi = fact_lines.merge(dim_prod, on="product_id", how="left").groupby("category").agg(
    lines=("order_id", "count"),
    order_qty=("order_qty", "sum"),
    delivery_qty=("delivery_qty", "sum"),
    lifr=("in_full_line", "mean"),
).reset_index()
prod_kpi["vofr"] = prod_kpi["delivery_qty"] / prod_kpi["order_qty"] * 100
prod_kpi["lifr"] *= 100
prod_kpi = prod_kpi.sort_values("lines", ascending=False)
prod_kpi.to_csv(f"{OUT_DIR}/category_kpis.csv", index=False)
print(prod_kpi.to_string(index=False))

print("\n=== PER-PRODUCT KPIs (top/bottom by fill rate) ===")
product_kpi = fact_lines.merge(dim_prod, on="product_id", how="left").groupby(
    ["product_id", "product_name", "category"]).agg(
    lines=("order_id", "count"),
    order_qty=("order_qty", "sum"),
    delivery_qty=("delivery_qty", "sum"),
    lifr=("in_full_line", "mean"),
    on_time_line=("on_time_line", "mean"),
).reset_index()
product_kpi["vofr"] = product_kpi["delivery_qty"] / product_kpi["order_qty"] * 100
product_kpi["lifr"] *= 100
product_kpi["on_time_line"] *= 100
product_kpi.to_csv(f"{OUT_DIR}/product_kpis.csv", index=False)

# ---------------------------------------------------------------------------
# 5. Monthly trend
# ---------------------------------------------------------------------------
print("\n=== MONTHLY TREND ===")
monthly = fact_agg.groupby("month").agg(
    orders=("order_id", "count"),
    ot_pct=("on_time", "mean"),
    if_pct=("in_full", "mean"),
    otif_pct=("otif", "mean"),
).reset_index()
monthly[["ot_pct", "if_pct", "otif_pct"]] *= 100
monthly["month"] = monthly["month"].astype(str)
monthly.to_csv(f"{OUT_DIR}/monthly_trend.csv", index=False)
print(monthly.to_string(index=False))

# ---------------------------------------------------------------------------
# 6. Delay analysis (late deliveries at line level)
# ---------------------------------------------------------------------------
print("\n=== DELAY ANALYSIS ===")
fact_lines["delay_days"] = (
    fact_lines["actual_delivery_date"] - fact_lines["agreed_delivery_date"]
).dt.days
late_lines = fact_lines[fact_lines["delay_days"] > 0]
print(f"  Total lines: {len(fact_lines):,}")
print(f"  Late lines (delay_days>0): {len(late_lines):,} "
      f"({len(late_lines)/len(fact_lines)*100:.1f}%)")
if len(late_lines) > 0:
    print(f"  Avg delay when late: {late_lines['delay_days'].mean():.2f} days")
    print(f"  Max delay: {late_lines['delay_days'].max()} days")

# Late-day distribution
delay_dist = fact_lines[fact_lines["delay_days"] >= 0]["delay_days"].value_counts(
    sort=False).reset_index()
delay_dist.columns = ["delay_days", "line_count"]
delay_dist.to_csv(f"{OUT_DIR}/delay_distribution.csv", index=False)

# ---------------------------------------------------------------------------
# 7. High-volume customers with worst OTIF (the "problem customers")
# ---------------------------------------------------------------------------
print("\n=== HIGH-VOLUME CUSTOMERS BY OTIF (worst first among top-half volume) ===")
volume_threshold = cust_kpi["orders"].median()
big = cust_kpi[cust_kpi["orders"] >= volume_threshold].sort_values("otif_pct")
print(big[["customer_name", "city", "orders", "ot_pct", "if_pct",
          "otif_pct", "otif_target%", "otif_variance"]].head(10).to_string(index=False))

# Save full late-customer ranking
cust_kpi.sort_values("otif_pct").to_csv(f"{OUT_DIR}/customer_kpis_ranked.csv", index=False)

# ===========================================================================
# CHARTS
# ===========================================================================
print("\nGenerating charts...")

# --- Chart 1: Overall KPIs vs typical 95% service benchmark ---
fig, ax = plt.subplots(figsize=(7, 4))
metrics = kpi_summary["metric"].tolist()
vals = kpi_summary["value_pct"].tolist()
colors = ["#2ecc71" if v >= 95 else ("#f39c12" if v >= 80 else "#e74c3c") for v in vals]
bars = ax.bar(metrics, vals, color=colors)
ax.axhline(95, ls="--", color="#555", lw=1, label="95% service benchmark")
ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_title("Overall Service-Level KPIs")
ax.set_ylabel("Percent")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 1.5, f"{v:.1f}%",
            ha="center", va="bottom", fontsize=9, fontweight="bold")
ax.legend(loc="lower right", fontsize=8)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/01_overall_kpis.png")
plt.close()

# --- Chart 2: Monthly trend of OT%, IF%, OTIF% ---
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(monthly["month"], monthly["ot_pct"], marker="o", label="OT%", lw=2)
ax.plot(monthly["month"], monthly["if_pct"], marker="s", label="IF%", lw=2)
ax.plot(monthly["month"], monthly["otif_pct"], marker="^", label="OTIF%", lw=2)
ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_title("Monthly Trend — OT%, IF%, OTIF%")
ax.set_ylabel("Percent")
ax.set_xlabel("Month")
ax.legend()
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/02_monthly_trend.png")
plt.close()

# --- Chart 3: OTIF% actual vs target by customer (top 15 by volume) ---
top15 = cust_kpi.head(15).sort_values("otif_pct")
fig, ax = plt.subplots(figsize=(9, 6))
y = np.arange(len(top15))
ax.barh(y - 0.2, top15["otif_pct"], height=0.4, label="OTIF% actual", color="#3498db")
ax.barh(y + 0.2, top15["otif_target%"], height=0.4, label="OTIF% target", color="#bdc3c7")
ax.set_yticks(y)
ax.set_yticklabels(top15["customer_name"] + " (" + top15["city"] + ")", fontsize=8)
ax.xaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_title("OTIF% Actual vs Target — Top 15 Customers by Order Volume")
ax.set_xlabel("Percent")
ax.legend(loc="lower right")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/03_otif_actual_vs_target.png")
plt.close()

# --- Chart 4: City performance ---
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(city_kpi))
w = 0.27
ax.bar(x - w, city_kpi["ot_pct"], w, label="OT%", color="#2ecc71")
ax.bar(x, city_kpi["if_pct"], w, label="IF%", color="#f39c12")
ax.bar(x + w, city_kpi["otif_pct"], w, label="OTIF%", color="#e74c3c")
ax.set_xticks(x)
ax.set_xticklabels(city_kpi["city"])
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_title("Service Levels by City")
ax.set_ylabel("Percent")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/04_city_performance.png")
plt.close()

# --- Chart 5: Category LIFR vs VOFR ---
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(prod_kpi))
w = 0.4
ax.bar(x - w/2, prod_kpi["lifr"], w, label="LIFR", color="#9b59b6")
ax.bar(x + w/2, prod_kpi["vofr"], w, label="VOFR", color="#1abc9c")
ax.set_xticks(x)
ax.set_xticklabels(prod_kpi["category"])
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_ylim(0, 105)
ax.set_title("Line Fill Rate vs Volume Fill Rate by Product Category")
ax.set_ylabel("Percent")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/05_category_fill_rates.png")
plt.close()

# --- Chart 6: Delay-day distribution (only 0-7 days) ---
dd = delay_dist[(delay_dist["delay_days"] >= 0) & (delay_dist["delay_days"] <= 7)]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(dd["delay_days"], dd["line_count"], color="#e67e22")
ax.set_title("Distribution of Delivery Delay (days) — order lines")
ax.set_xlabel("Delay (days past agreed date); 0 = on-time")
ax.set_ylabel("Number of order lines")
for i, r in dd.iterrows():
    ax.text(r["delay_days"], r["line_count"], f'{int(r["line_count"]):,}',
            ha="center", va="bottom", fontsize=8)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/06_delay_distribution.png")
plt.close()

# --- Chart 7: Volume-weighted OTIF scatter (customer) ---
fig, ax = plt.subplots(figsize=(8, 5.5))
sc = ax.scatter(cust_kpi["orders"], cust_kpi["otif_pct"],
                c=cust_kpi["otif_variance"], cmap="RdYlGn",
                s=70, edgecolor="k", linewidth=0.4, vmin=-30, vmax=5)
ax.axhline(cust_kpi["otif_pct"].mean(), ls="--", color="#555", lw=1,
           label=f"Mean OTIF% {cust_kpi['otif_pct'].mean():.1f}%")
for _, r in cust_kpi.iterrows():
    ax.annotate(r["customer_name"], (r["orders"], r["otif_pct"]),
                fontsize=6.5, alpha=0.75,
                xytext=(3, 3), textcoords="offset points")
ax.set_title("Order Volume vs OTIF% by Customer (color = OTIF variance vs target)")
ax.set_xlabel("Number of orders")
ax.set_ylabel("OTIF%")
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
plt.colorbar(sc, label="OTIF% variance vs target")
ax.legend(loc="lower right")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/07_volume_vs_otif_scatter.png")
plt.close()

print(f"\nAll charts saved to {CHART_DIR}")
print("Analysis exports saved to", OUT_DIR)
print("\nDONE.")
