-- ============================================================================
-- OlistIQ PostgreSQL Analytical & BI Views
-- High-Performance Standardized Reporting Views (Preventing Join Multiplication)
-- ============================================================================

-- 1. VIEW: bi_monthly_sales
-- Aggregates monthly product sales, freight revenue, total GMV, and volume.
CREATE OR REPLACE VIEW bi_monthly_sales AS
WITH order_item_totals AS (
    SELECT 
        fo.order_id,
        TO_CHAR(fo.order_purchase_timestamp, 'YYYY-MM') AS year_month,
        DATE_TRUNC('month', fo.order_purchase_timestamp)::DATE AS month_date,
        SUM(foi.price) AS order_product_sales,
        SUM(foi.freight_value) AS order_freight_value,
        SUM(foi.total_item_value) AS order_gmv,
        COUNT(foi.order_item_id) AS items_in_order
    FROM fact_orders fo
    JOIN fact_order_items foi ON fo.order_id = foi.order_id
    WHERE fo.order_status <> 'canceled'
    GROUP BY fo.order_id, TO_CHAR(fo.order_purchase_timestamp, 'YYYY-MM'), DATE_TRUNC('month', fo.order_purchase_timestamp)::DATE
),
monthly_agg AS (
    SELECT 
        year_month,
        month_date,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(items_in_order) AS total_units_sold,
        SUM(order_product_sales) AS total_product_sales,
        SUM(order_freight_value) AS total_freight_revenue,
        SUM(order_gmv) AS total_gmv,
        ROUND(AVG(order_gmv), 2) AS average_order_value
    FROM order_item_totals
    GROUP BY year_month, month_date
)
SELECT 
    year_month,
    month_date,
    total_orders,
    total_units_sold,
    total_product_sales,
    total_freight_revenue,
    total_gmv,
    average_order_value,
    ROUND(
        (total_gmv - LAG(total_gmv, 1) OVER (ORDER BY month_date)) / 
        NULLIF(LAG(total_gmv, 1) OVER (ORDER BY month_date), 0) * 100.0, 
        2
    ) AS mom_gmv_growth_pct,
    ROUND(
        (total_orders - LAG(total_orders, 1) OVER (ORDER BY month_date)) / 
        NULLIF(LAG(total_orders, 1) OVER (ORDER BY month_date), 0)::NUMERIC * 100.0, 
        2
    ) AS mom_orders_growth_pct
FROM monthly_agg;

-- 2. VIEW: bi_category_performance
-- Category revenue, units sold, AOV, seller count, and revenue share
CREATE OR REPLACE VIEW bi_category_performance AS
WITH cat_sales AS (
    SELECT 
        dp.category_display_name AS category,
        COUNT(DISTINCT foi.order_id) AS orders_count,
        COUNT(foi.order_item_id) AS units_sold,
        COUNT(DISTINCT foi.seller_id) AS active_sellers_count,
        SUM(foi.price) AS product_sales,
        SUM(foi.freight_value) AS freight_revenue,
        SUM(foi.total_item_value) AS category_gmv,
        ROUND(AVG(foi.price), 2) AS avg_item_price
    FROM fact_order_items foi
    JOIN fact_orders fo ON foi.order_id = fo.order_id
    JOIN dim_products dp ON foi.product_id = dp.product_id
    WHERE fo.order_status <> 'canceled'
    GROUP BY dp.category_display_name
)
SELECT 
    category,
    orders_count,
    units_sold,
    active_sellers_count,
    product_sales,
    freight_revenue,
    category_gmv,
    avg_item_price,
    ROUND(category_gmv / SUM(category_gmv) OVER () * 100.0, 2) AS revenue_share_pct,
    DENSE_RANK() OVER (ORDER BY category_gmv DESC) AS revenue_rank
FROM cat_sales;

-- 3. VIEW: bi_delivery_performance
-- Logistics efficiency: on-time rates, average delay, regional delivery times
CREATE OR REPLACE VIEW bi_delivery_performance AS
SELECT 
    dc.state AS customer_state,
    COUNT(fd.order_id) AS total_delivered_orders,
    SUM(fd.is_on_time) AS on_time_deliveries,
    SUM(fd.is_late) AS late_deliveries,
    ROUND(SUM(fd.is_on_time)::NUMERIC / NULLIF(COUNT(fd.order_id), 0) * 100.0, 2) AS on_time_delivery_rate_pct,
    ROUND(AVG(fd.delivery_duration_days), 2) AS avg_delivery_duration_days,
    ROUND(AVG(fd.carrier_delivery_days), 2) AS avg_carrier_transit_days,
    ROUND(AVG(fd.delivery_delay_days), 2) AS avg_delivery_delay_days
FROM fact_delivery fd
JOIN fact_orders fo ON fd.order_id = fo.order_id
JOIN dim_customers dc ON fo.customer_id = dc.customer_id
GROUP BY dc.state;

-- 4. VIEW: bi_payment_analysis
-- Payment method distribution, transaction volumes, installments
CREATE OR REPLACE VIEW bi_payment_analysis AS
WITH payment_summary AS (
    SELECT 
        payment_type,
        COUNT(order_id) AS payment_transactions,
        COUNT(DISTINCT order_id) AS orders_count,
        SUM(payment_value) AS total_payment_value,
        ROUND(AVG(payment_value), 2) AS avg_transaction_value,
        ROUND(AVG(payment_installments), 1) AS avg_installments
    FROM fact_payments
    GROUP BY payment_type
)
SELECT 
    payment_type,
    payment_transactions,
    orders_count,
    total_payment_value,
    avg_transaction_value,
    avg_installments,
    ROUND(total_payment_value / SUM(total_payment_value) OVER () * 100.0, 2) AS payment_share_pct
FROM payment_summary;

-- 5. VIEW: bi_customer_reviews
-- Review score distribution, CSAT, sentiment breakdown
CREATE OR REPLACE VIEW bi_customer_reviews AS
SELECT 
    fr.review_score,
    fr.sentiment,
    COUNT(fr.review_id) AS total_reviews,
    ROUND(COUNT(fr.review_id)::NUMERIC / SUM(COUNT(fr.review_id)) OVER () * 100.0, 2) AS review_percentage
FROM fact_reviews fr
GROUP BY fr.review_score, fr.sentiment;

-- 6. VIEW: bi_seller_performance
-- Top sellers by GMV, volume, and rating
CREATE OR REPLACE VIEW bi_seller_performance AS
SELECT 
    ds.seller_id,
    ds.city AS seller_city,
    ds.state AS seller_state,
    COUNT(DISTINCT foi.order_id) AS total_orders,
    COUNT(foi.order_item_id) AS total_units_sold,
    SUM(foi.total_item_value) AS total_seller_gmv,
    ROUND(AVG(foi.price), 2) AS avg_item_price,
    ROUND(AVG(fr.review_score), 2) AS avg_seller_review_score,
    DENSE_RANK() OVER (ORDER BY SUM(foi.total_item_value) DESC) AS seller_revenue_rank
FROM fact_order_items foi
JOIN dim_sellers ds ON foi.seller_id = ds.seller_id
LEFT JOIN fact_reviews fr ON foi.order_id = fr.order_id
GROUP BY ds.seller_id, ds.city, ds.state;

-- 7. VIEW: bi_executive_overview
-- Unified multi-metric KPI view for executive consumption
CREATE OR REPLACE VIEW bi_executive_overview AS
SELECT 
    (SELECT COUNT(DISTINCT order_id) FROM fact_orders WHERE order_status <> 'canceled') AS total_completed_orders,
    (SELECT COUNT(DISTINCT customer_unique_id) FROM dim_customers) AS total_unique_customers,
    (SELECT COUNT(DISTINCT seller_id) FROM dim_sellers) AS active_sellers,
    (SELECT SUM(total_item_value) FROM fact_order_items foi JOIN fact_orders fo ON foi.order_id = fo.order_id WHERE fo.order_status <> 'canceled') AS gross_merchandise_value,
    (SELECT ROUND(AVG(total_item_value), 2) FROM fact_order_items foi JOIN fact_orders fo ON foi.order_id = fo.order_id WHERE fo.order_status <> 'canceled') AS avg_order_item_value,
    (SELECT ROUND(SUM(is_on_time)::NUMERIC / NULLIF(COUNT(order_id), 0) * 100.0, 2) FROM fact_delivery) AS on_time_delivery_rate_pct,
    (SELECT ROUND(AVG(review_score), 2) FROM fact_reviews) AS overall_average_csat;
