"""
OlistIQ - Analytics Master Engine
Executes all specialized analytics modules:
1. Sales Analytics
2. Customer Intelligence & RFM
3. Logistics & Delivery SLAs
4. Customer Experience & CSAT Correlation
5. Payment Instruments & Financing
6. Statistical Forecasting
Generates the comprehensive Executive Business Insights Report.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import json
import logging
from datetime import datetime, timezone
from src.analytics.sales_analytics import compute_sales_metrics
from src.analytics.customer_analytics import compute_customer_analytics
from src.analytics.logistics_analytics import compute_logistics_metrics
from src.analytics.customer_experience import compute_cx_metrics
from src.analytics.payment_analytics import compute_payment_metrics
from src.analytics.forecasting import run_sales_forecasting

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.AnalyticsEngine")

DOCS_DIR = Path("docs")

def run_all_analytics() -> dict:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Starting complete OlistIQ Python analytics pipeline...")
    
    start_ts = datetime.now(timezone.utc).isoformat()
    
    sales_res = compute_sales_metrics()
    cust_res = compute_customer_analytics()
    log_res = compute_logistics_metrics()
    cx_res = compute_cx_metrics()
    pay_res = compute_payment_metrics()
    fc_res = run_sales_forecasting()
    
    consolidated = {
        "execution_timestamp": start_ts,
        "sales": sales_res,
        "customers": cust_res,
        "logistics": log_res,
        "customer_experience": cx_res,
        "payments": pay_res,
        "forecasting": fc_res
    }
    
    # Generate business_insights.md
    insights_path = DOCS_DIR / "business_insights.md"
    with open(insights_path, "w", encoding="utf-8") as f:
        f.write("# OlistIQ — Executive Business Intelligence & Insights Report\n\n")
        f.write(f"- **Execution Timestamp**: `{start_ts}`\n")
        f.write(f"- **Scope**: Brazilian E-Commerce Operations Analysis (Olist)\n\n")
        
        f.write("## 1. Executive Commercial Summary\n\n")
        f.write(f"- **Gross Merchandise Value (GMV)**: **R$ {sales_res['kpis']['total_gmv']:,.2f}**\n")
        f.write(f"- **Product Sales Value**: **R$ {sales_res['kpis']['total_product_sales']:,.2f}**\n")
        f.write(f"- **Freight Revenue**: **R$ {sales_res['kpis']['total_freight_revenue']:,.2f}** ({round(sales_res['kpis']['total_freight_revenue']/sales_res['kpis']['total_gmv']*100, 1)}% of GMV)\n")
        f.write(f"- **Total Completed Orders**: **{sales_res['kpis']['total_orders']:,}**\n")
        f.write(f"- **Average Order Value (AOV)**: **R$ {sales_res['kpis']['average_order_value']:.2f}**\n")
        f.write(f"- **Total Units Sold**: **{sales_res['kpis']['total_units_sold']:,}**\n")
        f.write(f"- **Average Item Price**: **R$ {sales_res['kpis']['average_item_price']:.2f}**\n\n")
        
        f.write("## 2. Customer Behavior & Retention Dynamics\n\n")
        f.write(f"- **Total Unique Customers**: **{cust_res['total_unique_customers']:,}**\n")
        f.write(f"- **Repeat Buyers**: **{cust_res['repeat_customers']:,}** (**{cust_res['repeat_customer_rate_pct']}%** repeat rate)\n")
        f.write(f"- **Synthetically Projected CLV**: **R$ {cust_res['clv_estimation']['estimated_clv_brl']:.2f}**\n")
        f.write(f"  > *Caveat*: {cust_res['clv_estimation']['assumptions']['limitation_statement']}\n\n")
        
        f.write("### Top Customer Segments (RFM Model)\n\n")
        f.write("| Segment | Customers | Customer % | Total GMV (R$) | Revenue % | Avg Recency (Days) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for seg in cust_res["top_segments"]:
            f.write(f"| **{seg['rfm_segment']}** | {seg['customer_count']:,} | {seg['customer_pct']}% | R$ {seg['total_revenue']:,.2f} | {seg['revenue_pct']}% | {seg['avg_recency_days']} |\n")
        f.write("\n")
        
        f.write("## 3. Logistics, Fulfillment & Delivery SLAs\n\n")
        f.write(f"- **On-Time Delivery Rate**: **{log_res['logistics_kpis']['on_time_delivery_rate_pct']}%** (Target: >95%)\n")
        f.write(f"- **Late Delivery Rate**: **{log_res['logistics_kpis']['late_delivery_rate_pct']}%**\n")
        f.write(f"- **Average End-to-End Delivery Duration**: **{log_res['logistics_kpis']['avg_delivery_duration_days']} days** (Median: {log_res['logistics_kpis']['median_delivery_duration_days']} days)\n")
        f.write(f"- **Average Carrier Transit Duration**: **{log_res['logistics_kpis']['avg_carrier_transit_days']} days**\n")
        f.write(f"- **Average Delay When Late**: **+{log_res['logistics_kpis']['avg_days_late']} days beyond SLA**\n")
        f.write(f"- **Eligible Delivery Cohort (Denominator)**: **{log_res['denominators']['eligible_delivered_orders']:,} delivered orders**\n\n")

        f.write("## 4. Customer Experience & Statistical Drivers of CSAT\n\n")
        f.write(f"- **Average CSAT Rating**: **{cx_res['csat_kpis']['average_csat']} / 5.0** (Median: {cx_res['csat_kpis']['median_csat']})\n")
        f.write(f"- **Promoter Review Rate (4-5 Stars)**: **{cx_res['csat_kpis']['promoter_rate_pct']}%**\n")
        f.write(f"- **Negative Review Rate (1-2 Stars)**: **{cx_res['csat_kpis']['negative_review_rate_pct']}%**\n")
        f.write(f"- **Average CSAT for On-Time Deliveries**: **{cx_res['correlation_analysis']['behavioral_impact']['avg_csat_on_time_orders']} / 5.0**\n")
        f.write(f"- **Average CSAT for Late Deliveries**: **{cx_res['correlation_analysis']['behavioral_impact']['avg_csat_late_orders']} / 5.0** (Drop: **-{cx_res['correlation_analysis']['behavioral_impact']['csat_penalty_for_late_delivery']} stars**)\n")
        f.write(f"- **Spearman Correlation (Delay vs CSAT)**: `rho = {cx_res['correlation_analysis']['delivery_delay_vs_csat']['spearman_rho']}` (p < 0.001)\n")
        f.write(f"  > *Methodological Note*: {cx_res['correlation_analysis']['methodological_caveat']}\n\n")

        f.write("## 5. Payment Instruments & Financing Trends\n\n")
        f.write(f"- **Total Settled Value**: **R$ {pay_res['payment_kpis']['total_settled_payment_value']:,.2f}**\n")
        f.write(f"- **Multi-Payment Split Orders**: **{pay_res['payment_kpis']['split_payment_orders']:,}** ({pay_res['payment_kpis']['split_payment_order_pct']}% of paid orders)\n\n")
        f.write("| Payment Method | Transactions | Transaction % | Total Settled (R$) | Value % | Avg Installments |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for pm in pay_res["method_breakdown"]:
            f.write(f"| **{pm['payment_type'].title()}** | {pm['transaction_count']:,} | {pm['transaction_share_pct']}% | R$ {pm['total_value']:,.2f} | {pm['value_share_pct']}% | {pm['avg_installments']} |\n")
        f.write("\n")

        f.write("## 6. Sales Forecasting Model Benchmark\n\n")
        f.write(f"- **Historical Horizon**: {fc_res['diagnostics']['sample_size_months']} consecutive operational months\n")
        f.write(f"- **Stationarity**: Augmented Dickey-Fuller p-value = `{fc_res['diagnostics']['augmented_dickey_fuller']['p_value']}`\n\n")
        f.write("| Model Name | MAE (R$) | RMSE (R$) | MAPE (%) |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for m in fc_res["leaderboard"]:
            f.write(f"| **{m['model_name']}** | R$ {m['metrics']['mae']:,.2f} | R$ {m['metrics']['rmse']:,.2f} | {m['metrics']['mape_pct']}% |\n")
        f.write("\n")
        f.write(f"  > *Forecasting Disclaimer*: {fc_res['validation_caveat']}\n")

    logger.info(f"Consolidated business insights report written to {insights_path}")
    return consolidated

if __name__ == "__main__":
    run_all_analytics()
