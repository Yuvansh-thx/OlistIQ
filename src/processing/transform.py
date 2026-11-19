"""
OlistIQ - Data Cleaning & Dimensional Transformation Pipeline
Transforms raw Olist datasets into an enterprise-grade Star Schema:
Dimensions:
  - dim_customers (customer_id, customer_unique_id, zip_code_prefix, city, state)
  - dim_products (product_id, category_name_portuguese, category_name_english, dimensions, weight)
  - dim_sellers (seller_id, zip_code_prefix, city, state)
  - dim_geography (zip_code_prefix, latitude, longitude, city, state)
  - dim_date (date_key, full_date, year, quarter, month, month_name, week, day, is_weekend)
  - dim_payment_types (payment_type_id, payment_type_name)

Facts (Respective Grains):
  - fact_orders (order_id, customer_id, order_status, purchase_date_key, ...) [Grain: 1 row per order]
  - fact_order_items (order_id, order_item_id, product_id, seller_id, price, freight, total_item_value) [Grain: 1 row per item]
  - fact_payments (order_id, payment_sequential, payment_type, installments, payment_value) [Grain: 1 row per payment transaction]
  - fact_reviews (order_id, review_id, review_score, review_comment_title, review_creation_date, sentiment_category) [Grain: 1 row per review]
  - fact_delivery (order_id, purchase_date, carrier_date, delivered_customer_date, estimated_delivery_date, delivery_duration_days, delivery_delay_days, is_on_time) [Grain: 1 row per delivered order]
"""

import logging
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.Transform")

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
CSV_EXPORT_DIR = Path("data/processed/csv")

def clean_and_transform() -> dict:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    CSV_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading raw CSV source files...")
    orders_df = pd.read_csv(RAW_DIR / "olist_orders_dataset.csv")
    items_df = pd.read_csv(RAW_DIR / "olist_order_items_dataset.csv")
    customers_df = pd.read_csv(RAW_DIR / "olist_customers_dataset.csv")
    products_df = pd.read_csv(RAW_DIR / "olist_products_dataset.csv")
    payments_df = pd.read_csv(RAW_DIR / "olist_order_payments_dataset.csv")
    reviews_df = pd.read_csv(RAW_DIR / "olist_order_reviews_dataset.csv")
    sellers_df = pd.read_csv(RAW_DIR / "olist_sellers_dataset.csv")
    geo_df = pd.read_csv(RAW_DIR / "olist_geolocation_dataset.csv")
    trans_df = pd.read_csv(RAW_DIR / "product_category_name_translation.csv")
    
    # -------------------------------------------------------------
    # 1. DIM_GEOGRAPHY (Aggregation & Outlier Treatment)
    # -------------------------------------------------------------
    logger.info("Processing DIM_GEOGRAPHY: Aggregating 1M raw coordinates to unique zip centroids...")
    # Filter Brazil bounding box: lat in [-33.75, +5.27], lng in [-73.98, -34.79]
    valid_geo = geo_df[
        (geo_df["geolocation_lat"].between(-33.75, 5.27)) &
        (geo_df["geolocation_lng"].between(-73.98, -34.79))
    ].copy()
    
    # Clean city text (uppercase, trimmed)
    valid_geo["geolocation_city"] = valid_geo["geolocation_city"].str.strip().str.title()
    valid_geo["geolocation_state"] = valid_geo["geolocation_state"].str.strip().str.upper()
    
    # Aggregate by zip_code_prefix: median lat/lng + mode for city and state
    geo_agg = valid_geo.groupby("geolocation_zip_code_prefix").agg(
        latitude=("geolocation_lat", "median"),
        longitude=("geolocation_lng", "median"),
        city=("geolocation_city", lambda s: s.mode().iloc[0] if not s.empty else "Unknown"),
        state=("geolocation_state", lambda s: s.mode().iloc[0] if not s.empty else "Unknown")
    ).reset_index()
    
    geo_agg.rename(columns={"geolocation_zip_code_prefix": "zip_code_prefix"}, inplace=True)
    # Ensure rounded coordinates for storage precision (4 decimal places ~ 11 meters)
    geo_agg["latitude"] = geo_agg["latitude"].round(4)
    geo_agg["longitude"] = geo_agg["longitude"].round(4)
    logger.info(f"DIM_GEOGRAPHY created with {len(geo_agg):,} unique zip codes (98% reduction from 1M raw pings).")
    
    # -------------------------------------------------------------
    # 2. DIM_PRODUCTS (Category Translation & Metric Sanitization)
    # -------------------------------------------------------------
    logger.info("Processing DIM_PRODUCTS: Joining English translations and imputing missing attributes...")
    prod_merged = pd.merge(
        products_df,
        trans_df,
        on="product_category_name",
        how="left"
    )
    
    prod_merged["category_name_portuguese"] = prod_merged["product_category_name"].fillna("desconhecido")
    prod_merged["category_name_english"] = prod_merged["product_category_name_english"].fillna("unknown_category")
    # Clean string formatting (replace underscores with spaces, Title Case)
    prod_merged["category_display_name"] = prod_merged["category_name_english"].str.replace("_", " ").str.title()
    
    # Fill physical dimensions medians
    for col in ["product_name_lenght", "product_description_lenght", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]:
        prod_merged[col] = prod_merged[col].fillna(prod_merged[col].median())
        
    dim_products = prod_merged[[
        "product_id",
        "category_name_portuguese",
        "category_name_english",
        "category_display_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    ]].copy()
    
    dim_products.rename(columns={
        "product_name_lenght": "name_length",
        "product_description_lenght": "description_length",
        "product_photos_qty": "photos_qty",
        "product_weight_g": "weight_g",
        "product_length_cm": "length_cm",
        "product_height_cm": "height_cm",
        "product_width_cm": "width_cm"
    }, inplace=True)
    
    # -------------------------------------------------------------
    # 3. DIM_CUSTOMERS & DIM_SELLERS
    # -------------------------------------------------------------
    logger.info("Processing DIM_CUSTOMERS and DIM_SELLERS...")
    dim_customers = customers_df[[
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state"
    ]].copy()
    dim_customers.rename(columns={
        "customer_zip_code_prefix": "zip_code_prefix",
        "customer_city": "city",
        "customer_state": "state"
    }, inplace=True)
    dim_customers["city"] = dim_customers["city"].str.strip().str.title()
    dim_customers["state"] = dim_customers["state"].str.strip().str.upper()
    
    dim_sellers = sellers_df[[
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state"
    ]].copy()
    dim_sellers.rename(columns={
        "seller_zip_code_prefix": "zip_code_prefix",
        "seller_city": "city",
        "seller_state": "state"
    }, inplace=True)
    dim_sellers["city"] = dim_sellers["city"].str.strip().str.title()
    dim_sellers["state"] = dim_sellers["state"].str.strip().str.upper()

    # -------------------------------------------------------------
    # 4. DIM_DATE (Standard Enterprise Analytical Date Dimension)
    # -------------------------------------------------------------
    logger.info("Generating standard DIM_DATE (2016-01-01 to 2018-12-31)...")
    date_range = pd.date_range(start="2016-01-01", end="2018-12-31", freq="D")
    dim_date = pd.DataFrame({"full_date": date_range})
    dim_date["date_key"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["year_quarter"] = dim_date["year"].astype(str) + "-Q" + dim_date["quarter"].astype(str)
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["month_name"] = dim_date["full_date"].dt.strftime("%B")
    dim_date["year_month"] = dim_date["full_date"].dt.strftime("%Y-%m")
    dim_date["week_of_year"] = dim_date["full_date"].dt.isocalendar().week.astype(int)
    dim_date["day_of_month"] = dim_date["full_date"].dt.day
    dim_date["day_of_week"] = dim_date["full_date"].dt.dayofweek + 1  # 1 = Monday, 7 = Sunday
    dim_date["day_name"] = dim_date["full_date"].dt.strftime("%A")
    dim_date["is_weekend"] = dim_date["day_of_week"].isin([6, 7]).astype(int)

    # -------------------------------------------------------------
    # 5. DIM_PAYMENT_TYPES
    # -------------------------------------------------------------
    payment_types = sorted(payments_df["payment_type"].unique())
    dim_payment_types = pd.DataFrame({
        "payment_type_id": range(1, len(payment_types) + 1),
        "payment_type_name": payment_types
    })

    # -------------------------------------------------------------
    # 6. FACT_ORDERS & FACT_DELIVERY
    # -------------------------------------------------------------
    logger.info("Processing FACT_ORDERS and FACT_DELIVERY...")
    orders_clean = orders_df.copy()
    date_fields = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
    for df_col in date_fields:
        orders_clean[df_col] = pd.to_datetime(orders_clean[df_col], errors="coerce")
        
    orders_clean["purchase_date_key"] = orders_clean["order_purchase_timestamp"].dt.strftime("%Y%m%d").fillna(19000101).astype(int)
    
    # Grain: 1 record per order
    fact_orders = orders_clean[[
        "order_id",
        "customer_id",
        "order_status",
        "purchase_date_key",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]].copy()
    
    # FACT_DELIVERY: Dedicated to logistics analysis, avoiding null distortions
    # Filtering to completed deliveries with valid delivery dates
    delivered_orders = orders_clean[
        (orders_clean["order_status"] == "delivered") &
        (orders_clean["order_delivered_customer_date"].notnull())
    ].copy()
    
    delivered_orders["delivery_duration_days"] = (
        (delivered_orders["order_delivered_customer_date"] - delivered_orders["order_purchase_timestamp"]).dt.total_seconds() / 86400.0
    ).round(2)
    
    delivered_orders["carrier_delivery_days"] = (
        (delivered_orders["order_delivered_customer_date"] - delivered_orders["order_delivered_carrier_date"]).dt.total_seconds() / 86400.0
    ).round(2)
    
    delivered_orders["delivery_delay_days"] = (
        (delivered_orders["order_delivered_customer_date"] - delivered_orders["order_estimated_delivery_date"]).dt.total_seconds() / 86400.0
    ).round(2)
    
    # Positive delay = late; <= 0 = on-time
    delivered_orders["is_late"] = (delivered_orders["delivery_delay_days"] > 0).astype(int)
    delivered_orders["is_on_time"] = (delivered_orders["delivery_delay_days"] <= 0).astype(int)
    
    fact_delivery = delivered_orders[[
        "order_id",
        "order_purchase_timestamp",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "delivery_duration_days",
        "carrier_delivery_days",
        "delivery_delay_days",
        "is_on_time",
        "is_late"
    ]].copy()

    # -------------------------------------------------------------
    # 7. FACT_ORDER_ITEMS (Grain: 1 record per order item)
    # -------------------------------------------------------------
    logger.info("Processing FACT_ORDER_ITEMS...")
    fact_order_items = items_df[[
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value"
    ]].copy()
    
    fact_order_items["total_item_value"] = (fact_order_items["price"] + fact_order_items["freight_value"]).round(2)
    fact_order_items["price"] = fact_order_items["price"].round(2)
    fact_order_items["freight_value"] = fact_order_items["freight_value"].round(2)

    # -------------------------------------------------------------
    # 8. FACT_PAYMENTS (Grain: 1 record per payment transaction)
    # -------------------------------------------------------------
    logger.info("Processing FACT_PAYMENTS...")
    fact_payments = payments_df[[
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value"
    ]].copy()
    fact_payments["payment_value"] = fact_payments["payment_value"].round(2)

    # -------------------------------------------------------------
    # 9. FACT_REVIEWS (Grain: 1 record per review; deduplicated)
    # -------------------------------------------------------------
    logger.info("Processing FACT_REVIEWS...")
    reviews_clean = reviews_df.copy()
    reviews_clean["review_creation_date"] = pd.to_datetime(reviews_clean["review_creation_date"], errors="coerce")
    reviews_clean["review_answer_timestamp"] = pd.to_datetime(reviews_clean["review_answer_timestamp"], errors="coerce")
    
    # Sort by answer timestamp and drop duplicates on composite (review_id, order_id)
    reviews_clean = reviews_clean.sort_values("review_answer_timestamp").drop_duplicates(subset=["review_id", "order_id"], keep="last")
    
    # Sentiment classification
    def get_sentiment(score):
        if score >= 4:
            return "Positive"
        elif score == 3:
            return "Neutral"
        else:
            return "Negative"
            
    reviews_clean["sentiment"] = reviews_clean["review_score"].apply(get_sentiment)
    
    fact_reviews = reviews_clean[[
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
        "sentiment"
    ]].copy()

    # -------------------------------------------------------------
    # 10. Persistence: Save as Parquet & CSV
    # -------------------------------------------------------------
    tables = {
        "dim_customers": dim_customers,
        "dim_products": dim_products,
        "dim_sellers": dim_sellers,
        "dim_geography": geo_agg,
        "dim_date": dim_date,
        "dim_payment_types": dim_payment_types,
        "fact_orders": fact_orders,
        "fact_order_items": fact_order_items,
        "fact_payments": fact_payments,
        "fact_reviews": fact_reviews,
        "fact_delivery": fact_delivery
    }
    
    summary = {}
    for tbl_name, tbl_df in tables.items():
        parquet_file = PROCESSED_DIR / f"{tbl_name}.parquet"
        csv_file = CSV_EXPORT_DIR / f"{tbl_name}.csv"
        
        tbl_df.to_parquet(parquet_file, index=False)
        tbl_df.to_csv(csv_file, index=False)
        
        size_mb = round(parquet_file.stat().st_size / (1024 * 1024), 2)
        summary[tbl_name] = {
            "rows": len(tbl_df),
            "columns": len(tbl_df.columns),
            "parquet_size_mb": size_mb
        }
        logger.info(f"Saved {tbl_name}: {len(tbl_df):,} rows, {len(tbl_df.columns)} cols -> {parquet_file}")
        
    return summary

if __name__ == "__main__":
    clean_and_transform()
