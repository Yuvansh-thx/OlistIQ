"""
OlistIQ - Customer Analytics Module
Calculates:
- Customer Lifetime Purchase Frequency & Repeat Purchase Rate
- Standardized RFM Segmentation (Recency, Frequency, Monetary)
- Monthly Customer Acquisition Cohort Retention Matrix
- Estimated Customer Lifetime Value (CLV) with explicit assumptions documented
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.CustomerAnalytics")

PROCESSED_DIR = Path("data/processed")
EXPORTS_DIR = Path("data/exports")

def compute_customer_analytics() -> dict:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading processed datasets for customer intelligence...")
    orders = pd.read_parquet(PROCESSED_DIR / "fact_orders.parquet")
    items = pd.read_parquet(PROCESSED_DIR / "fact_order_items.parquet")
    customers = pd.read_parquet(PROCESSED_DIR / "dim_customers.parquet")
    
    # Exclude canceled orders
    valid_orders = orders[orders["order_status"] != "canceled"].copy()
    valid_orders["purchase_datetime"] = pd.to_datetime(valid_orders["order_purchase_timestamp"])
    
    # Join with customers to obtain customer_unique_id
    order_customer = valid_orders.merge(
        customers[["customer_id", "customer_unique_id", "city", "state"]],
        on="customer_id",
        how="inner"
    )
    
    # Order monetary values
    order_values = items.groupby("order_id")["total_item_value"].sum().reset_index()
    order_customer = order_customer.merge(order_values, on="order_id", how="left")
    order_customer["total_item_value"] = order_customer["total_item_value"].fillna(0)

    # -------------------------------------------------------------
    # 1. Purchase Frequency & Repeat Customer Rate
    # -------------------------------------------------------------
    customer_summary = order_customer.groupby("customer_unique_id").agg(
        orders_count=("order_id", "nunique"),
        total_spent=("total_item_value", "sum"),
        first_purchase=("purchase_datetime", "min"),
        last_purchase=("purchase_datetime", "max")
    ).reset_index()
    
    total_unique_customers = len(customer_summary)
    repeat_customers = customer_summary[customer_summary["orders_count"] > 1]
    repeat_customer_count = len(repeat_customers)
    repeat_customer_rate = round(repeat_customer_count / total_unique_customers * 100.0, 2)
    
    logger.info(
        f"Customer Base: {total_unique_customers:,} unique buyers | "
        f"Repeat Buyers: {repeat_customer_count:,} ({repeat_customer_rate}%)"
    )

    # -------------------------------------------------------------
    # 2. RFM Analysis & Segmentation
    # -------------------------------------------------------------
    # Reference snapshot date: 1 day after the latest transaction in the dataset
    snapshot_date = order_customer["purchase_datetime"].max() + pd.Timedelta(days=1)
    
    customer_summary["recency_days"] = (snapshot_date - customer_summary["last_purchase"]).dt.days
    customer_summary["frequency"] = customer_summary["orders_count"]
    customer_summary["monetary"] = customer_summary["total_spent"].round(2)
    
    # Score 1-5 quantization:
    # Recency: Lower days = Higher Score (Quintiles)
    customer_summary["r_score"] = pd.qcut(customer_summary["recency_days"], q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    
    # Frequency: Because >96% of customers have frequency=1, standard quintiles collapse.
    # We apply explicit business thresholding for frequency:
    # 1 order = score 1; 2 orders = score 3; 3-4 orders = score 4; >=5 orders = score 5
    def score_frequency(f):
        if f >= 4:
            return 5
        elif f == 3:
            return 4
        elif f == 2:
            return 3
        else:
            return 1
            
    customer_summary["f_score"] = customer_summary["frequency"].apply(score_frequency)
    
    # Monetary: Quintiles
    customer_summary["m_score"] = pd.qcut(customer_summary["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # RFM Segment Classification Rules
    def assign_rfm_segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif f >= 3 and m >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2 and m >= 3:
            return "Potential Loyalists"
        elif r == 5 and f == 1:
            return "New Recent Customers"
        elif r == 4 and f == 1:
            return "Promising"
        elif r == 3 and f >= 2:
            return "Need Attention"
        elif r == 2 and f <= 2:
            return "About to Sleep"
        elif r <= 2 and f >= 3:
            return "At Risk"
        elif r <= 2 and f == 1 and m <= 2:
            return "Hibernating"
        else:
            return "Lost Customers"
            
    customer_summary["rfm_segment"] = customer_summary.apply(assign_rfm_segment, axis=1)
    
    segment_distribution = customer_summary.groupby("rfm_segment").agg(
        customer_count=("customer_unique_id", "count"),
        total_revenue=("monetary", "sum"),
        avg_recency_days=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean")
    ).reset_index()
    
    segment_distribution["customer_pct"] = (segment_distribution["customer_count"] / total_unique_customers * 100).round(2)
    segment_distribution["revenue_pct"] = (segment_distribution["total_revenue"] / customer_summary["monetary"].sum() * 100).round(2)
    segment_distribution["total_revenue"] = segment_distribution["total_revenue"].round(2)
    segment_distribution["avg_recency_days"] = segment_distribution["avg_recency_days"].round(1)
    segment_distribution["avg_frequency"] = segment_distribution["avg_frequency"].round(2)
    segment_distribution["avg_monetary"] = segment_distribution["avg_monetary"].round(2)
    segment_distribution = segment_distribution.sort_values("total_revenue", ascending=False).reset_index(drop=True)
    
    # Save RFM exports
    rfm_export_path = EXPORTS_DIR / "bi_customer_segments.csv"
    customer_summary[[
        "customer_unique_id", "recency_days", "frequency", "monetary",
        "r_score", "f_score", "m_score", "rfm_segment"
    ]].to_csv(rfm_export_path, index=False)
    
    segment_agg_path = EXPORTS_DIR / "bi_segment_summary.csv"
    segment_distribution.to_csv(segment_agg_path, index=False)

    # -------------------------------------------------------------
    # 3. Customer Cohort Retention Analysis
    # -------------------------------------------------------------
    logger.info("Computing monthly customer acquisition cohort matrix...")
    order_customer["order_month"] = order_customer["purchase_datetime"].dt.to_period("M")
    
    # Customer cohort group: Month of first purchase
    customer_first_month = order_customer.groupby("customer_unique_id")["order_month"].min().reset_index()
    customer_first_month.rename(columns={"order_month": "cohort_month"}, inplace=True)
    
    cohort_df = order_customer.merge(customer_first_month, on="customer_unique_id")
    cohort_df["cohort_index"] = (cohort_df["order_month"].dt.year - cohort_df["cohort_month"].dt.year) * 12 + \
                                (cohort_df["order_month"].dt.month - cohort_df["cohort_month"].dt.month)
                                
    cohort_counts = cohort_df.groupby(["cohort_month", "cohort_index"])["customer_unique_id"].nunique().reset_index()
    cohort_pivot = cohort_counts.pivot(index="cohort_month", columns="cohort_index", values="customer_unique_id")
    cohort_size = cohort_pivot.iloc[:, 0]
    retention_matrix = cohort_pivot.divide(cohort_size, axis=0).mul(100).round(2)
    
    retention_matrix_path = EXPORTS_DIR / "bi_customer_cohorts.csv"
    retention_matrix.reset_index().to_csv(retention_matrix_path, index=False)

    # -------------------------------------------------------------
    # 4. Projected Customer Lifetime Value (CLV) with Explicit Assumptions
    # -------------------------------------------------------------
    # Assumptions documented:
    # 1. Historical dataset represents an observational window from Sept 2016 - Sept 2018 (24 months).
    # 2. Average Order Value (AOV) = Platform Mean Spend per order.
    # 3. Purchase Frequency = Mean annual order rate.
    # 4. Estimated Gross Margin = 20% standard e-commerce retail benchmark.
    # 5. Annual Churn Rate estimated at 80% based on repeat rate of 3.12%.
    avg_order_value = float(customer_summary["monetary"].sum() / customer_summary["frequency"].sum())
    purchase_frequency_annual = float(customer_summary["frequency"].mean() * (365.0 / 730.0)) # annualized
    gross_margin_rate = 0.20
    annual_churn_rate = 0.80
    
    estimated_clv = round((avg_order_value * purchase_frequency_annual * gross_margin_rate) / annual_churn_rate, 2)
    
    clv_meta = {
        "metric_name": "Projected Estimated Customer Lifetime Value (CLV)",
        "estimated_clv_brl": estimated_clv,
        "assumptions": {
            "observational_window_months": 24,
            "average_order_value_brl": round(avg_order_value, 2),
            "purchase_frequency_annual": round(purchase_frequency_annual, 3),
            "estimated_gross_margin_pct": 20.0,
            "estimated_annual_churn_rate_pct": 80.0,
            "limitation_statement": (
                "Notice: This is a synthetic projection. The Olist dataset spans only 2 years with a high proportion "
                "of single-transaction marketplace buyers. Actual empirical CLV requires multi-year persistent user tracking."
            )
        }
    }

    return {
        "total_unique_customers": total_unique_customers,
        "repeat_customers": repeat_customer_count,
        "repeat_customer_rate_pct": repeat_customer_rate,
        "top_segments": segment_distribution.head(5).to_dict(orient="records"),
        "clv_estimation": clv_meta
    }

if __name__ == "__main__":
    compute_customer_analytics()
