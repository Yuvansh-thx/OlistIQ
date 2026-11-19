"""
OlistIQ - Logistics & Delivery Analytics Module
Calculates:
- End-to-end Order-to-Delivery Cycle Time (days)
- Carrier transit duration vs seller fulfillment duration
- On-Time Delivery Rate & SLA Late Breach Rate
- Estimated vs Actual Delivery Discrepancies
- Regional & Seller Logistics Performance
- Excludes canceled/undelivered orders; documents exact denominators.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.LogisticsAnalytics")

PROCESSED_DIR = Path("data/processed")
EXPORTS_DIR = Path("data/exports")

def compute_logistics_metrics() -> dict:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading logistics dataset...")
    delivery = pd.read_parquet(PROCESSED_DIR / "fact_delivery.parquet")
    orders = pd.read_parquet(PROCESSED_DIR / "fact_orders.parquet")
    customers = pd.read_parquet(PROCESSED_DIR / "dim_customers.parquet")
    items = pd.read_parquet(PROCESSED_DIR / "fact_order_items.parquet")
    sellers = pd.read_parquet(PROCESSED_DIR / "dim_sellers.parquet")
    
    # Denominator documentation
    total_orders = len(orders)
    delivered_orders_count = len(delivery)
    
    # 1. Platform-wide Delivery Performance Metrics
    on_time_orders_count = int(delivery["is_on_time"].sum())
    late_orders_count = int(delivery["is_late"].sum())
    
    on_time_delivery_rate = round(on_time_orders_count / delivered_orders_count * 100.0, 2)
    late_delivery_rate = round(late_orders_count / delivered_orders_count * 100.0, 2)
    
    avg_delivery_duration_days = round(float(delivery["delivery_duration_days"].mean()), 2)
    median_delivery_duration_days = round(float(delivery["delivery_duration_days"].median()), 2)
    avg_carrier_transit_days = round(float(delivery["carrier_delivery_days"].dropna().mean()), 2)
    
    # When late, how late?
    late_deliveries = delivery[delivery["is_late"] == 1]
    avg_days_late = round(float(late_deliveries["delivery_delay_days"].mean()), 2) if len(late_deliveries) > 0 else 0.0
    
    # Early deliveries: Delivered before estimated date
    early_deliveries = delivery[delivery["is_on_time"] == 1]
    avg_days_early = round(float(abs(early_deliveries["delivery_delay_days"]).mean()), 2)

    logger.info(
        f"Logistics Overview: Delivered Orders: {delivered_orders_count:,} | "
        f"On-Time Rate: {on_time_delivery_rate}% | Avg Delivery Time: {avg_delivery_duration_days} days | "
        f"Avg Days Early: {avg_days_early} days | Avg Days Late (when late): {avg_days_late} days"
    )

    # 2. Regional Delivery Performance (Customer State)
    delivery_orders = delivery.merge(orders[["order_id", "customer_id"]], on="order_id", how="inner")
    delivery_cust = delivery_orders.merge(customers[["customer_id", "state", "city"]], on="customer_id", how="inner")
    
    regional_logistics = delivery_cust.groupby("state").agg(
        total_delivered=("order_id", "count"),
        on_time_orders=("is_on_time", "sum"),
        late_orders=("is_late", "sum"),
        avg_duration_days=("delivery_duration_days", "mean"),
        median_duration_days=("delivery_duration_days", "median"),
        avg_carrier_days=("carrier_delivery_days", "mean")
    ).reset_index()
    
    regional_logistics["on_time_rate_pct"] = (regional_logistics["on_time_orders"] / regional_logistics["total_delivered"] * 100).round(2)
    regional_logistics["late_rate_pct"] = (regional_logistics["late_orders"] / regional_logistics["total_delivered"] * 100).round(2)
    regional_logistics["avg_duration_days"] = regional_logistics["avg_duration_days"].round(2)
    regional_logistics["median_duration_days"] = regional_logistics["median_duration_days"].round(2)
    regional_logistics["avg_carrier_days"] = regional_logistics["avg_carrier_days"].round(2)
    regional_logistics = regional_logistics.sort_values("total_delivered", ascending=False).reset_index(drop=True)
    
    regional_export_path = EXPORTS_DIR / "bi_delivery_performance.csv"
    regional_logistics.to_csv(regional_export_path, index=False)

    # 3. Seller Fulfillment & Shipping Limit SLA Compliance
    item_orders = items.merge(orders[["order_id", "order_delivered_carrier_date"]], on="order_id", how="inner")
    item_orders["carrier_ts"] = pd.to_datetime(item_orders["order_delivered_carrier_date"])
    item_orders["shipping_limit_ts"] = pd.to_datetime(item_orders["shipping_limit_date"])
    
    valid_carrier_items = item_orders[item_orders["carrier_ts"].notnull()].copy()
    valid_carrier_items["seller_shipped_on_time"] = (valid_carrier_items["carrier_ts"] <= valid_carrier_items["shipping_limit_ts"]).astype(int)
    
    seller_sla = valid_carrier_items.groupby("seller_id").agg(
        total_shipped_items=("order_item_id", "count"),
        on_time_shipped_items=("seller_shipped_on_time", "sum")
    ).reset_index()
    
    seller_sla["seller_sla_compliance_pct"] = (seller_sla["on_time_shipped_items"] / seller_sla["total_shipped_items"] * 100).round(2)
    seller_sla = seller_sla.merge(sellers[["seller_id", "state", "city"]], on="seller_id", how="left")
    seller_sla = seller_sla.sort_values("total_shipped_items", ascending=False).reset_index(drop=True)
    
    seller_export_path = EXPORTS_DIR / "bi_seller_fulfillment_sla.csv"
    seller_sla.to_csv(seller_export_path, index=False)

    return {
        "denominators": {
            "total_orders_in_database": total_orders,
            "eligible_delivered_orders": delivered_orders_count,
            "exclusion_rationale": "Canceled, invoiced, processing, or undelivered orders have no customer receipt date and are excluded from delivery duration calculations."
        },
        "logistics_kpis": {
            "on_time_delivery_rate_pct": on_time_delivery_rate,
            "late_delivery_rate_pct": late_delivery_rate,
            "avg_delivery_duration_days": avg_delivery_duration_days,
            "median_delivery_duration_days": median_delivery_duration_days,
            "avg_carrier_transit_days": avg_carrier_transit_days,
            "avg_days_early": avg_days_early,
            "avg_days_late": avg_days_late
        },
        "top_states_logistics": regional_logistics.head(5).to_dict(orient="records")
    }

if __name__ == "__main__":
    compute_logistics_metrics()
