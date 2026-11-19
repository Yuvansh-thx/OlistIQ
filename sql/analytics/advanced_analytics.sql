-- ============================================================================
-- OlistIQ Advanced SQL Analytics Suite
-- 13 Production Business Queries (CTEs, Window Functions, Retention Cohorts)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Monthly GMV, MoM Growth & Running Total
-- ----------------------------------------------------------------------------
WITH monthly_orders AS (
    SELECT 
        strftime('%Y-%m', fo.order_purchase_timestamp) AS year_month,
        SUM(foi.total_item_value) AS monthly_gmv,
        COUNT(DISTINCT fo.order_id) AS monthly_orders
    FROM fact_orders fo
    JOIN fact_order_items foi ON fo.order_id = foi.order_id
    WHERE fo.order_status <> 'canceled'
    GROUP BY strftime('%Y-%m', fo.order_purchase_timestamp)
)
SELECT 
    year_month,
    ROUND(monthly_gmv, 2) AS monthly_gmv,
    monthly_orders,
    ROUND(
        (monthly_gmv - LAG(monthly_gmv, 1) OVER (ORDER BY year_month)) /
        NULLIF(LAG(monthly_gmv, 1) OVER (ORDER BY year_month), 0) * 100.0,
        2
    ) AS mom_gmv_growth_pct,
    ROUND(SUM(monthly_gmv) OVER (ORDER BY year_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_total_gmv,
    ROUND(AVG(monthly_gmv) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m_gmv
FROM monthly_orders
ORDER BY year_month;

-- ----------------------------------------------------------------------------
-- 2. Monthly Order Volume & Moving Average
-- ----------------------------------------------------------------------------
WITH monthly_vol AS (
    SELECT 
        strftime('%Y-%m', order_purchase_timestamp) AS year_month,
        COUNT(order_id) AS order_volume
    FROM fact_orders
    WHERE order_status <> 'canceled'
    GROUP BY strftime('%Y-%m', order_purchase_timestamp)
)
SELECT 
    year_month,
    order_volume,
    ROUND(
        (order_volume - LAG(order_volume, 1) OVER (ORDER BY year_month)) * 100.0 /
        NULLIF(LAG(order_volume, 1) OVER (ORDER BY year_month), 0),
        2
    ) AS mom_order_growth_pct,
    ROUND(AVG(order_volume) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS moving_avg_3m_orders
FROM monthly_vol
ORDER BY year_month;

-- ----------------------------------------------------------------------------
-- 3. Average Order Value (AOV) by Month
-- ----------------------------------------------------------------------------
SELECT 
    strftime('%Y-%m', fo.order_purchase_timestamp) AS year_month,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    ROUND(SUM(foi.total_item_value), 2) AS total_gmv,
    ROUND(SUM(foi.total_item_value) / COUNT(DISTINCT fo.order_id), 2) AS average_order_value
FROM fact_orders fo
JOIN fact_order_items foi ON fo.order_id = foi.order_id
WHERE fo.order_status <> 'canceled'
GROUP BY strftime('%Y-%m', fo.order_purchase_timestamp)
ORDER BY year_month;

-- ----------------------------------------------------------------------------
-- 4. Category Revenue Ranking & Pareto Contribution
-- ----------------------------------------------------------------------------
WITH category_totals AS (
    SELECT 
        dp.category_display_name AS category,
        ROUND(SUM(foi.total_item_value), 2) AS category_revenue,
        COUNT(foi.order_item_id) AS items_sold
    FROM fact_order_items foi
    JOIN fact_orders fo ON foi.order_id = fo.order_id
    JOIN dim_products dp ON foi.product_id = dp.product_id
    WHERE fo.order_status <> 'canceled'
    GROUP BY dp.category_display_name
),
ranked_categories AS (
    SELECT 
        category,
        category_revenue,
        items_sold,
        DENSE_RANK() OVER (ORDER BY category_revenue DESC) AS rev_rank,
        SUM(category_revenue) OVER () AS total_platform_revenue,
        SUM(category_revenue) OVER (ORDER BY category_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
    FROM category_totals
)
SELECT 
    rev_rank,
    category,
    category_revenue,
    items_sold,
    ROUND(category_revenue * 100.0 / total_platform_revenue, 2) AS revenue_share_pct,
    ROUND(cumulative_revenue * 100.0 / total_platform_revenue, 2) AS pareto_cumulative_share_pct
FROM ranked_categories
ORDER BY rev_rank
LIMIT 20;

-- ----------------------------------------------------------------------------
-- 5. Seller Revenue Ranking & Tiering
-- ----------------------------------------------------------------------------
WITH seller_sales AS (
    SELECT 
        ds.seller_id,
        ds.city AS seller_city,
        ds.state AS seller_state,
        ROUND(SUM(foi.total_item_value), 2) AS seller_gmv,
        COUNT(DISTINCT foi.order_id) AS orders_fulfilled,
        COUNT(foi.order_item_id) AS items_sold
    FROM fact_order_items foi
    JOIN fact_orders fo ON foi.order_id = fo.order_id
    JOIN dim_sellers ds ON foi.seller_id = ds.seller_id
    WHERE fo.order_status <> 'canceled'
    GROUP BY ds.seller_id, ds.city, ds.state
)
SELECT 
    DENSE_RANK() OVER (ORDER BY seller_gmv DESC) AS seller_rank,
    seller_id,
    seller_city,
    seller_state,
    seller_gmv,
    orders_fulfilled,
    items_sold,
    CASE 
        WHEN seller_gmv >= 100000 THEN 'Tier 1 - Diamond'
        WHEN seller_gmv >= 50000 THEN 'Tier 2 - Platinum'
        WHEN seller_gmv >= 10000 THEN 'Tier 3 - Gold'
        ELSE 'Tier 4 - Standard'
    END AS seller_tier
FROM seller_sales
ORDER BY seller_gmv DESC
LIMIT 25;

-- ----------------------------------------------------------------------------
-- 6. Customer Purchase Frequency Distribution
-- ----------------------------------------------------------------------------
WITH customer_orders AS (
    SELECT 
        dc.customer_unique_id,
        COUNT(DISTINCT fo.order_id) AS lifetime_orders,
        ROUND(SUM(foi.total_item_value), 2) AS lifetime_spend
    FROM dim_customers dc
    JOIN fact_orders fo ON dc.customer_id = fo.customer_id
    JOIN fact_order_items foi ON fo.order_id = foi.order_id
    WHERE fo.order_status <> 'canceled'
    GROUP BY dc.customer_unique_id
)
SELECT 
    lifetime_orders,
    COUNT(customer_unique_id) AS customer_count,
    ROUND(COUNT(customer_unique_id) * 100.0 / (SELECT COUNT(DISTINCT customer_unique_id) FROM dim_customers), 2) AS customer_pct,
    ROUND(SUM(lifetime_spend), 2) AS total_segment_spend,
    ROUND(AVG(lifetime_spend), 2) AS avg_spend_per_customer
FROM customer_orders
GROUP BY lifetime_orders
ORDER BY lifetime_orders;

-- ----------------------------------------------------------------------------
-- 7. Repeat Customer Analysis (One-time vs Repeat Buyers)
-- ----------------------------------------------------------------------------
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
    CASE WHEN total_orders > 1 THEN 'Repeat Customer' ELSE 'Single-Order Customer' END AS customer_loyalty_type,
    COUNT(customer_unique_id) AS total_customers,
    ROUND(COUNT(customer_unique_id) * 100.0 / SUM(COUNT(customer_unique_id)) OVER (), 2) AS customer_share_pct,
    ROUND(SUM(total_spend), 2) AS total_revenue_generated,
    ROUND(SUM(total_spend) * 100.0 / SUM(SUM(total_spend)) OVER (), 2) AS revenue_share_pct,
    ROUND(AVG(total_spend), 2) AS avg_customer_spend
FROM customer_order_summary
GROUP BY CASE WHEN total_orders > 1 THEN 'Repeat Customer' ELSE 'Single-Order Customer' END;

-- ----------------------------------------------------------------------------
-- 8. Payment Method Distribution & Installment Breakdown
-- ----------------------------------------------------------------------------
SELECT 
    payment_type,
    COUNT(order_id) AS transaction_count,
    ROUND(COUNT(order_id) * 100.0 / SUM(COUNT(order_id)) OVER (), 2) AS transaction_share_pct,
    ROUND(SUM(payment_value), 2) AS total_payment_value,
    ROUND(SUM(payment_value) * 100.0 / SUM(SUM(payment_value)) OVER (), 2) AS value_share_pct,
    ROUND(AVG(payment_value), 2) AS avg_transaction_size,
    ROUND(AVG(payment_installments), 1) AS avg_installments
FROM fact_payments
GROUP BY payment_type
ORDER BY total_payment_value DESC;

-- ----------------------------------------------------------------------------
-- 9. Delivery Delay & SLA Breach Analysis by State
-- ----------------------------------------------------------------------------
SELECT 
    dc.state AS customer_state,
    COUNT(fd.order_id) AS total_delivered_orders,
    SUM(fd.is_on_time) AS on_time_orders,
    SUM(fd.is_late) AS late_orders,
    ROUND(SUM(fd.is_on_time) * 100.0 / COUNT(fd.order_id), 2) AS on_time_rate_pct,
    ROUND(SUM(fd.is_late) * 100.0 / COUNT(fd.order_id), 2) AS late_rate_pct,
    ROUND(AVG(fd.delivery_duration_days), 2) AS avg_delivery_days,
    ROUND(AVG(CASE WHEN fd.is_late = 1 THEN fd.delivery_delay_days ELSE NULL END), 2) AS avg_delay_days_when_late
FROM fact_delivery fd
JOIN fact_orders fo ON fd.order_id = fo.order_id
JOIN dim_customers dc ON fo.customer_id = dc.customer_id
GROUP BY dc.state
ORDER BY total_delivered_orders DESC;

-- ----------------------------------------------------------------------------
-- 10. Review Score Distribution & Negative Review Rate
-- ----------------------------------------------------------------------------
SELECT 
    review_score,
    sentiment,
    COUNT(review_id) AS review_count,
    ROUND(COUNT(review_id) * 100.0 / SUM(COUNT(review_id)) OVER (), 2) AS review_share_pct,
    CASE 
        WHEN review_score IN (1, 2) THEN 'Detractor (Negative)'
        WHEN review_score = 3 THEN 'Passive (Neutral)'
        ELSE 'Promoter (Positive)'
    END AS nps_category
FROM fact_reviews
GROUP BY review_score, sentiment
ORDER BY review_score DESC;

-- ----------------------------------------------------------------------------
-- 11. Regional Sales Performance (State & Region Matrix)
-- ----------------------------------------------------------------------------
SELECT 
    dc.state AS customer_state,
    COUNT(DISTINCT fo.order_id) AS order_count,
    ROUND(SUM(foi.total_item_value), 2) AS state_gmv,
    ROUND(SUM(foi.total_item_value) * 100.0 / SUM(SUM(foi.total_item_value)) OVER (), 2) AS gmv_share_pct,
    ROUND(AVG(foi.total_item_value), 2) AS avg_order_item_value,
    ROUND(AVG(foi.freight_value), 2) AS avg_freight_value
FROM fact_orders fo
JOIN dim_customers dc ON fo.customer_id = dc.customer_id
JOIN fact_order_items foi ON fo.order_id = foi.order_id
WHERE fo.order_status <> 'canceled'
GROUP BY dc.state
ORDER BY state_gmv DESC;

-- ----------------------------------------------------------------------------
-- 12. Month-over-Month Growth & Velocity
-- ----------------------------------------------------------------------------
WITH monthly_summary AS (
    SELECT 
        strftime('%Y-%m', fo.order_purchase_timestamp) AS year_month,
        COUNT(DISTINCT fo.order_id) AS order_count,
        ROUND(SUM(foi.total_item_value), 2) AS gmv
    FROM fact_orders fo
    JOIN fact_order_items foi ON fo.order_id = foi.order_id
    WHERE fo.order_status <> 'canceled'
    GROUP BY strftime('%Y-%m', fo.order_purchase_timestamp)
)
SELECT 
    year_month,
    order_count,
    gmv,
    ROUND((gmv - LAG(gmv, 1) OVER (ORDER BY year_month)) * 100.0 / NULLIF(LAG(gmv, 1) OVER (ORDER BY year_month), 0), 2) AS gmv_growth_pct,
    ROUND((order_count - LAG(order_count, 1) OVER (ORDER BY year_month)) * 100.0 / NULLIF(LAG(order_count, 1) OVER (ORDER BY year_month), 0), 2) AS order_growth_pct
FROM monthly_summary
ORDER BY year_month;

-- ----------------------------------------------------------------------------
-- 13. Customer Cohort Retention (Acquisition Month vs Activity Month)
-- ----------------------------------------------------------------------------
WITH customer_first_purchase AS (
    SELECT 
        dc.customer_unique_id,
        MIN(strftime('%Y-%m', fo.order_purchase_timestamp)) AS cohort_month
    FROM dim_customers dc
    JOIN fact_orders fo ON dc.customer_id = fo.customer_id
    WHERE fo.order_status <> 'canceled'
    GROUP BY dc.customer_unique_id
),
customer_activities AS (
    SELECT 
        dc.customer_unique_id,
        cfp.cohort_month,
        strftime('%Y-%m', fo.order_purchase_timestamp) AS order_month
    FROM dim_customers dc
    JOIN customer_first_purchase cfp ON dc.customer_unique_id = cfp.customer_unique_id
    JOIN fact_orders fo ON dc.customer_id = fo.customer_id
    WHERE fo.order_status <> 'canceled'
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_unique_id) AS initial_users
    FROM customer_first_purchase
    GROUP BY cohort_month
)
SELECT 
    ca.cohort_month,
    cs.initial_users,
    ca.order_month,
    COUNT(DISTINCT ca.customer_unique_id) AS retained_users,
    ROUND(COUNT(DISTINCT ca.customer_unique_id) * 100.0 / cs.initial_users, 2) AS retention_rate_pct
FROM customer_activities ca
JOIN cohort_size cs ON ca.cohort_month = cs.cohort_month
GROUP BY ca.cohort_month, cs.initial_users, ca.order_month
HAVING ca.cohort_month >= '2017-01' AND ca.order_month >= '2017-01'
ORDER BY ca.cohort_month, ca.order_month;
