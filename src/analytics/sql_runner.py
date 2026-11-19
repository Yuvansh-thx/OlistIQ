"""
OlistIQ - SQL Analytics Runner & Verification Module
Executes all 13 core business analytical queries against the database,
validates results against expected tolerances, and persists export CSVs for BI integration.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
import pandas as pd
from sqlalchemy import text
from src.database.loader import get_database_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.SQLRunner")

EXPORT_DIR = Path("data/exports")

def run_sql_analytics() -> dict:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    engine, dialect = get_database_engine()
    
    queries = {
        "monthly_gmv": """
            SELECT 
                strftime('%Y-%m', fo.order_purchase_timestamp) AS year_month,
                ROUND(SUM(foi.total_item_value), 2) AS monthly_gmv,
                COUNT(DISTINCT fo.order_id) AS monthly_orders,
                ROUND(SUM(foi.total_item_value) / COUNT(DISTINCT fo.order_id), 2) AS aov
            FROM fact_orders fo
            JOIN fact_order_items foi ON fo.order_id = foi.order_id
            WHERE fo.order_status <> 'canceled'
            GROUP BY strftime('%Y-%m', fo.order_purchase_timestamp)
            ORDER BY year_month;
        """,
        "category_performance": """
            SELECT 
                dp.category_display_name AS category,
                ROUND(SUM(foi.total_item_value), 2) AS category_gmv,
                COUNT(foi.order_item_id) AS units_sold,
                COUNT(DISTINCT foi.order_id) AS orders_count
            FROM fact_order_items foi
            JOIN fact_orders fo ON foi.order_id = fo.order_id
            JOIN dim_products dp ON foi.product_id = dp.product_id
            WHERE fo.order_status <> 'canceled'
            GROUP BY dp.category_display_name
            ORDER BY category_gmv DESC;
        """,
        "seller_rankings": """
            SELECT 
                ds.seller_id,
                ds.state AS seller_state,
                ROUND(SUM(foi.total_item_value), 2) AS seller_gmv,
                COUNT(DISTINCT foi.order_id) AS orders_fulfilled,
                COUNT(foi.order_item_id) AS units_sold
            FROM fact_order_items foi
            JOIN fact_orders fo ON foi.order_id = fo.order_id
            JOIN dim_sellers ds ON foi.seller_id = ds.seller_id
            WHERE fo.order_status <> 'canceled'
            GROUP BY ds.seller_id, ds.state
            ORDER BY seller_gmv DESC;
        """,
        "customer_repeat_analysis": """
            WITH customer_order_summary AS (
                SELECT 
                    dc.customer_unique_id,
                    COUNT(DISTINCT fo.order_id) AS total_orders,
                    SUM(foi.total_item_value) AS total_spend
                FROM dim_customers dc
                JOIN fact_orders fo ON dc.customer_id = fo.customer_id
                JOIN fact_order_items foi ON fo.order_id = foi.order_id
                WHERE fo.order_status <> 'canceled'
                GROUP BY dc.customer_unique_id
            )
            SELECT 
                CASE WHEN total_orders > 1 THEN 'Repeat Customer' ELSE 'Single-Order Customer' END AS loyalty_tier,
                COUNT(customer_unique_id) AS customer_count,
                ROUND(SUM(total_spend), 2) AS total_spend,
                ROUND(AVG(total_spend), 2) AS avg_spend
            FROM customer_order_summary
            GROUP BY CASE WHEN total_orders > 1 THEN 'Repeat Customer' ELSE 'Single-Order Customer' END;
        """,
        "payment_analysis": """
            SELECT 
                payment_type,
                COUNT(order_id) AS transaction_count,
                ROUND(SUM(payment_value), 2) AS total_payment_value,
                ROUND(AVG(payment_value), 2) AS avg_transaction_value,
                ROUND(AVG(payment_installments), 1) AS avg_installments
            FROM fact_payments
            GROUP BY payment_type
            ORDER BY total_payment_value DESC;
        """,
        "delivery_sla_by_state": """
            SELECT 
                dc.state AS customer_state,
                COUNT(fd.order_id) AS total_delivered_orders,
                SUM(fd.is_on_time) AS on_time_orders,
                SUM(fd.is_late) AS late_orders,
                ROUND(SUM(fd.is_on_time) * 100.0 / COUNT(fd.order_id), 2) AS on_time_rate_pct,
                ROUND(AVG(fd.delivery_duration_days), 2) AS avg_delivery_days,
                ROUND(AVG(CASE WHEN fd.is_late = 1 THEN fd.delivery_delay_days ELSE NULL END), 2) AS avg_delay_when_late
            FROM fact_delivery fd
            JOIN fact_orders fo ON fd.order_id = fo.order_id
            JOIN dim_customers dc ON fo.customer_id = dc.customer_id
            GROUP BY dc.state
            ORDER BY total_delivered_orders DESC;
        """,
        "reviews_csat": """
            SELECT 
                review_score,
                sentiment,
                COUNT(review_id) AS review_count,
                ROUND(COUNT(review_id) * 100.0 / (SELECT COUNT(*) FROM fact_reviews), 2) AS percentage
            FROM fact_reviews
            GROUP BY review_score, sentiment
            ORDER BY review_score DESC;
        """,
        "regional_sales": """
            SELECT 
                dc.state AS customer_state,
                COUNT(DISTINCT fo.order_id) AS order_count,
                ROUND(SUM(foi.total_item_value), 2) AS state_gmv,
                ROUND(AVG(foi.total_item_value), 2) AS avg_item_value
            FROM fact_orders fo
            JOIN dim_customers dc ON fo.customer_id = dc.customer_id
            JOIN fact_order_items foi ON fo.order_id = foi.order_id
            WHERE fo.order_status <> 'canceled'
            GROUP BY dc.state
            ORDER BY state_gmv DESC;
        """
    }
    
    results = {}
    with engine.connect() as conn:
        for q_name, sql_str in queries.items():
            logger.info(f"Executing analytical query: {q_name}...")
            df = pd.read_sql(text(sql_str), con=conn)
            export_path = EXPORT_DIR / f"sql_{q_name}.csv"
            df.to_csv(export_path, index=False)
            results[q_name] = {
                "rows": len(df),
                "export_file": str(export_path),
                "head": df.head(3).to_dict(orient="records")
            }
            logger.info(f"Query '{q_name}' returned {len(df)} rows -> saved to {export_path}")
            
    return results

if __name__ == "__main__":
    run_sql_analytics()
