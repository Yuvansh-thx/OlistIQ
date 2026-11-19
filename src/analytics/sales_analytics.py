"""
OlistIQ - Sales Analytics Module
Calculates:
- Gross Merchandise Value (GMV)
- Product Sales Value (excluding freight)
- Freight Revenue
- Average Order Value (AOV)
- Monthly Sales & Growth Velocity
- Category & Regional Contributions
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.SalesAnalytics")

PROCESSED_DIR = Path("data/processed")
EXPORTS_DIR = Path("data/exports")

def compute_sales_metrics() -> dict:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading processed dimensional datasets for sales analysis...")
    orders = pd.read_parquet(PROCESSED_DIR / "fact_orders.parquet")
    items = pd.read_parquet(PROCESSED_DIR / "fact_order_items.parquet")
    customers = pd.read_parquet(PROCESSED_DIR / "dim_customers.parquet")
    products = pd.read_parquet(PROCESSED_DIR / "dim_products.parquet")
    
    # Filter valid completed/active orders (exclude cancelled)
    valid_orders = orders[orders["order_status"] != "canceled"].copy()
    valid_order_ids = set(valid_orders["order_id"])
    
    valid_items = items[items["order_id"].isin(valid_order_ids)].copy()
    
    # 1. Platform Totals
    total_orders_count = int(valid_orders["order_id"].nunique())
    total_units_sold = int(len(valid_items))
    total_product_sales = round(float(valid_items["price"].sum()), 2)
    total_freight_revenue = round(float(valid_items["freight_value"].sum()), 2)
    total_gmv = round(float(valid_items["total_item_value"].sum()), 2)
    average_order_value = round(total_gmv / total_orders_count, 2)
    average_item_price = round(total_product_sales / total_units_sold, 2)
    
    logger.info(f"Sales Summary: Total GMV: R$ {total_gmv:,.2f} | Orders: {total_orders_count:,} | AOV: R$ {average_order_value:.2f}")

    # 2. Monthly Trend & Growth Analysis
    merged_items = valid_items.merge(
        valid_orders[["order_id", "order_purchase_timestamp"]],
        on="order_id",
        how="inner"
    )
    merged_items["year_month"] = pd.to_datetime(merged_items["order_purchase_timestamp"]).dt.strftime("%Y-%m")
    
    monthly_sales = merged_items.groupby("year_month").agg(
        orders_count=("order_id", "nunique"),
        units_sold=("order_item_id", "count"),
        product_sales=("price", "sum"),
        freight_revenue=("freight_value", "sum"),
        total_gmv=("total_item_value", "sum")
    ).reset_index()
    
    monthly_sales["product_sales"] = monthly_sales["product_sales"].round(2)
    monthly_sales["freight_revenue"] = monthly_sales["freight_revenue"].round(2)
    monthly_sales["total_gmv"] = monthly_sales["total_gmv"].round(2)
    monthly_sales["aov"] = (monthly_sales["total_gmv"] / monthly_sales["orders_count"]).round(2)
    
    # MoM Growth
    monthly_sales["mom_gmv_growth_pct"] = monthly_sales["total_gmv"].pct_change().mul(100).round(2)
    monthly_sales["mom_orders_growth_pct"] = monthly_sales["orders_count"].pct_change().mul(100).round(2)
    
    monthly_sales_path = EXPORTS_DIR / "bi_monthly_sales.csv"
    monthly_sales.to_csv(monthly_sales_path, index=False)
    
    # 3. Category Revenue & Pareto Contribution
    items_with_prod = valid_items.merge(products[["product_id", "category_display_name"]], on="product_id", how="left")
    category_summary = items_with_prod.groupby("category_display_name").agg(
        category_gmv=("total_item_value", "sum"),
        product_sales=("price", "sum"),
        freight_revenue=("freight_value", "sum"),
        units_sold=("order_item_id", "count"),
        orders_count=("order_id", "nunique")
    ).reset_index()
    
    category_summary["category_gmv"] = category_summary["category_gmv"].round(2)
    category_summary["revenue_share_pct"] = (category_summary["category_gmv"] / total_gmv * 100).round(2)
    category_summary = category_summary.sort_values("category_gmv", ascending=False).reset_index(drop=True)
    category_summary["cumulative_share_pct"] = category_summary["revenue_share_pct"].cumsum().round(2)
    
    category_summary_path = EXPORTS_DIR / "bi_category_performance.csv"
    category_summary.to_csv(category_summary_path, index=False)
    
    # 4. Regional Revenue Performance
    orders_with_cust = valid_orders.merge(customers[["customer_id", "state", "city"]], on="customer_id", how="left")
    regional_merged = valid_items.merge(orders_with_cust[["order_id", "state", "city"]], on="order_id", how="inner")
    
    regional_summary = regional_merged.groupby("state").agg(
        state_gmv=("total_item_value", "sum"),
        orders_count=("order_id", "nunique"),
        units_sold=("order_item_id", "count"),
        avg_order_value=("total_item_value", lambda x: round(x.sum() / x.nunique(), 2))
    ).reset_index()
    
    regional_summary["state_gmv"] = regional_summary["state_gmv"].round(2)
    regional_summary["revenue_share_pct"] = (regional_summary["state_gmv"] / total_gmv * 100).round(2)
    regional_summary = regional_summary.sort_values("state_gmv", ascending=False).reset_index(drop=True)
    
    regional_summary_path = EXPORTS_DIR / "bi_regional_sales.csv"
    regional_summary.to_csv(regional_summary_path, index=False)

    return {
        "kpis": {
            "total_orders": total_orders_count,
            "total_units_sold": total_units_sold,
            "total_product_sales": total_product_sales,
            "total_freight_revenue": total_freight_revenue,
            "total_gmv": total_gmv,
            "average_order_value": average_order_value,
            "average_item_price": average_item_price
        },
        "monthly_sales_head": monthly_sales.head(3).to_dict(orient="records"),
        "top_5_categories": category_summary.head(5).to_dict(orient="records"),
        "top_5_states": regional_summary.head(5).to_dict(orient="records")
    }

if __name__ == "__main__":
    compute_sales_metrics()
