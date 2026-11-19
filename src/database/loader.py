"""
OlistIQ - Database Engineering & Ingestion Loader Module
Connects to Supabase PostgreSQL (via SQLAlchemy & psycopg) or fallback analytical store.
Executes DDL migrations, creates tables, indexes, constraints, and views.
Performs batch bulk-loading of cleaned dimension and fact datasets.
Prevents duplicate loads through idempotent truncate-and-load / upsert semantics.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.Database")

load_dotenv()

PROCESSED_DIR = Path("data/processed")
SCHEMA_DIR = Path("sql/schema")
VIEWS_DIR = Path("sql/views")

def get_database_engine() -> tuple[Engine, str]:
    """
    Resolves connection to Supabase PostgreSQL via environment variables.
    Falls back to local analytical SQLite database if Supabase credentials are unconfigured,
    ensuring 100% reproducible local testing without blocker.
    """
    host = os.getenv("SUPABASE_DB_HOST")
    user = os.getenv("SUPABASE_DB_USER")
    password = os.getenv("SUPABASE_DB_PASSWORD")
    port = os.getenv("SUPABASE_DB_PORT", "5432")
    dbname = os.getenv("SUPABASE_DB_NAME", "postgres")
    direct_url = os.getenv("DATABASE_URL")

    if direct_url:
        logger.info("Connecting via DATABASE_URL environment variable...")
        return create_engine(direct_url), "postgresql"
    elif host and user and password:
        logger.info(f"Connecting to Supabase PostgreSQL at {host}:{port}/{dbname} (User: {user})...")
        # Connection string using psycopg v3 driver
        conn_str = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
        return create_engine(conn_str, pool_pre_ping=True), "postgresql"
    else:
        logger.warning(
            "Supabase credentials not detected in .env. "
            "Initializing local SQLite analytical database at 'data/olist_analytical.db' for continuous verification."
        )
        db_path = Path("data/olist_analytical.db")
        return create_engine(f"sqlite:///{db_path}"), "sqlite"

def run_migrations(engine: Engine, dialect: str):
    """Executes DDL migration scripts and creates views."""
    logger.info(f"Running database migrations for dialect: {dialect}...")
    
    with engine.begin() as conn:
        if dialect == "postgresql":
            # Read schema files
            for sql_file in sorted(SCHEMA_DIR.glob("*.sql")):
                logger.info(f"Applying schema migration: {sql_file.name}")
                with open(sql_file, "r", encoding="utf-8") as f:
                    statements = f.read()
                conn.execute(text(statements))
                
            for view_file in sorted(VIEWS_DIR.glob("*.sql")):
                logger.info(f"Applying view migration: {view_file.name}")
                with open(view_file, "r", encoding="utf-8") as f:
                    statements = f.read()
                conn.execute(text(statements))
        else:
            # SQLite simplified schema adaptation
            logger.info("Creating tables in local analytical SQLite engine...")
            pass # Handled dynamically during pandas to_sql or explicit DDL

def load_star_schema(engine: Engine, dialect: str) -> dict:
    """Loads all dimensional and fact parquet datasets into the database."""
    table_order = [
        "dim_date",
        "dim_geography",
        "dim_customers",
        "dim_products",
        "dim_sellers",
        "dim_payment_types",
        "fact_orders",
        "fact_order_items",
        "fact_payments",
        "fact_reviews",
        "fact_delivery"
    ]
    
    results = {}
    logger.info("Initiating bulk loading of dimensional star schema...")
    
    with engine.connect() as conn:
        for tbl in table_order:
            parquet_path = PROCESSED_DIR / f"{tbl}.parquet"
            if not parquet_path.exists():
                raise FileNotFoundError(f"Missing transformed dataset: {parquet_path}. Run cleaning first!")
                
            df = pd.read_parquet(parquet_path)
            
            # Idempotent write: replace mode for dimensions & facts
            logger.info(f"Loading table '{tbl}' ({len(df):,} rows)...")
            df.to_sql(
                name=tbl,
                con=engine,
                if_exists="replace",
                index=False,
                chunksize=5000,
                method="multi" if dialect == "postgresql" else None
            )
            
            # Verify record count in database
            result = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            results[tbl] = int(result)
            logger.info(f"Verified '{tbl}' in database: {result:,} records successfully loaded.")
            
    # If SQLite, also create the standard BI views
    if dialect == "sqlite":
        _create_sqlite_views(engine)
        
    return results

def _create_sqlite_views(engine: Engine):
    """Creates SQLite-compatible versions of the analytical views."""
    views = [
        """
        CREATE VIEW IF NOT EXISTS bi_monthly_sales AS
        SELECT 
            strftime('%Y-%m', fo.order_purchase_timestamp) AS year_month,
            COUNT(DISTINCT fo.order_id) AS total_orders,
            COUNT(foi.order_item_id) AS total_units_sold,
            ROUND(SUM(foi.price), 2) AS total_product_sales,
            ROUND(SUM(foi.freight_value), 2) AS total_freight_revenue,
            ROUND(SUM(foi.total_item_value), 2) AS total_gmv,
            ROUND(AVG(foi.total_item_value), 2) AS average_order_value
        FROM fact_orders fo
        JOIN fact_order_items foi ON fo.order_id = foi.order_id
        WHERE fo.order_status <> 'canceled'
        GROUP BY strftime('%Y-%m', fo.order_purchase_timestamp);
        """,
        """
        CREATE VIEW IF NOT EXISTS bi_category_performance AS
        SELECT 
            dp.category_display_name AS category,
            COUNT(DISTINCT foi.order_id) AS orders_count,
            COUNT(foi.order_item_id) AS units_sold,
            COUNT(DISTINCT foi.seller_id) AS active_sellers_count,
            ROUND(SUM(foi.price), 2) AS product_sales,
            ROUND(SUM(foi.freight_value), 2) AS freight_revenue,
            ROUND(SUM(foi.total_item_value), 2) AS category_gmv,
            ROUND(AVG(foi.price), 2) AS avg_item_price
        FROM fact_order_items foi
        JOIN fact_orders fo ON foi.order_id = fo.order_id
        JOIN dim_products dp ON foi.product_id = dp.product_id
        WHERE fo.order_status <> 'canceled'
        GROUP BY dp.category_display_name;
        """,
        """
        CREATE VIEW IF NOT EXISTS bi_delivery_performance AS
        SELECT 
            dc.state AS customer_state,
            COUNT(fd.order_id) AS total_delivered_orders,
            SUM(fd.is_on_time) AS on_time_deliveries,
            SUM(fd.is_late) AS late_deliveries,
            ROUND(SUM(fd.is_on_time) * 100.0 / COUNT(fd.order_id), 2) AS on_time_delivery_rate_pct,
            ROUND(AVG(fd.delivery_duration_days), 2) AS avg_delivery_duration_days,
            ROUND(AVG(fd.carrier_delivery_days), 2) AS avg_carrier_transit_days,
            ROUND(AVG(fd.delivery_delay_days), 2) AS avg_delivery_delay_days
        FROM fact_delivery fd
        JOIN fact_orders fo ON fd.order_id = fo.order_id
        JOIN dim_customers dc ON fo.customer_id = dc.customer_id
        GROUP BY dc.state;
        """,
        """
        CREATE VIEW IF NOT EXISTS bi_payment_analysis AS
        SELECT 
            payment_type,
            COUNT(order_id) AS payment_transactions,
            COUNT(DISTINCT order_id) AS orders_count,
            ROUND(SUM(payment_value), 2) AS total_payment_value,
            ROUND(AVG(payment_value), 2) AS avg_transaction_value,
            ROUND(AVG(payment_installments), 1) AS avg_installments
        FROM fact_payments
        GROUP BY payment_type;
        """,
        """
        CREATE VIEW IF NOT EXISTS bi_customer_reviews AS
        SELECT 
            review_score,
            sentiment,
            COUNT(review_id) AS total_reviews,
            ROUND(COUNT(review_id) * 100.0 / (SELECT COUNT(*) FROM fact_reviews), 2) AS review_percentage
        FROM fact_reviews
        GROUP BY review_score, sentiment;
        """,
        """
        CREATE VIEW IF NOT EXISTS bi_executive_overview AS
        SELECT 
            (SELECT COUNT(DISTINCT order_id) FROM fact_orders WHERE order_status <> 'canceled') AS total_completed_orders,
            (SELECT COUNT(DISTINCT customer_unique_id) FROM dim_customers) AS total_unique_customers,
            (SELECT COUNT(DISTINCT seller_id) FROM dim_sellers) AS active_sellers,
            (SELECT ROUND(SUM(total_item_value), 2) FROM fact_order_items foi JOIN fact_orders fo ON foi.order_id = fo.order_id WHERE fo.order_status <> 'canceled') AS gross_merchandise_value,
            (SELECT ROUND(AVG(total_item_value), 2) FROM fact_order_items foi JOIN fact_orders fo ON foi.order_id = fo.order_id WHERE fo.order_status <> 'canceled') AS avg_order_item_value,
            (SELECT ROUND(SUM(is_on_time) * 100.0 / COUNT(order_id), 2) FROM fact_delivery) AS on_time_delivery_rate_pct,
            (SELECT ROUND(AVG(review_score), 2) FROM fact_reviews) AS overall_average_csat;
        """
    ]
    with engine.begin() as conn:
        for v_sql in views:
            conn.execute(text(v_sql))
    logger.info("Standard analytical BI views verified in analytical store.")

def main():
    engine, dialect = get_database_engine()
    run_migrations(engine, dialect)
    load_star_schema(engine, dialect)
    logger.info("Database migration and loading stage finished successfully.")

if __name__ == "__main__":
    main()
