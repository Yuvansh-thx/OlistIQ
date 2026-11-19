-- ============================================================================
-- OlistIQ PostgreSQL Schema Migration: 02_create_facts.sql
-- Star Schema Fact Tables (Preserving Respective Grains)
-- ============================================================================

-- 1. FACT_ORDERS (Grain: 1 row per order)
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL REFERENCES dim_customers(customer_id),
    order_status VARCHAR(25) NOT NULL,
    purchase_date_key INT NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_orders_customer ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_orders_status ON fact_orders(order_status);
CREATE INDEX IF NOT EXISTS idx_fact_orders_purchase_ts ON fact_orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_fact_orders_date_key ON fact_orders(purchase_date_key);

-- 2. FACT_ORDER_ITEMS (Grain: 1 row per item in order)
CREATE TABLE IF NOT EXISTS fact_order_items (
    order_id VARCHAR(32) NOT NULL REFERENCES fact_orders(order_id),
    order_item_id INT NOT NULL,
    product_id VARCHAR(32) NOT NULL REFERENCES dim_products(product_id),
    seller_id VARCHAR(32) NOT NULL REFERENCES dim_sellers(seller_id),
    shipping_limit_date TIMESTAMPTZ NOT NULL,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(10,2) NOT NULL CHECK (freight_value >= 0),
    total_item_value NUMERIC(10,2) NOT NULL CHECK (total_item_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_items_product ON fact_order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_items_seller ON fact_order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_fact_items_order ON fact_order_items(order_id);

-- 3. FACT_PAYMENTS (Grain: 1 row per payment transaction)
CREATE TABLE IF NOT EXISTS fact_payments (
    order_id VARCHAR(32) NOT NULL REFERENCES fact_orders(order_id),
    payment_sequential INT NOT NULL,
    payment_type VARCHAR(50) NOT NULL,
    payment_installments INT NOT NULL CHECK (payment_installments >= 0),
    payment_value NUMERIC(10,2) NOT NULL CHECK (payment_value >= 0),
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE INDEX IF NOT EXISTS idx_fact_payments_order ON fact_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_fact_payments_type ON fact_payments(payment_type);

-- 4. FACT_REVIEWS (Grain: 1 row per review)
CREATE TABLE IF NOT EXISTS fact_reviews (
    review_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL REFERENCES fact_orders(order_id),
    review_score INT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMPTZ,
    review_answer_timestamp TIMESTAMPTZ,
    sentiment VARCHAR(15) NOT NULL,
    PRIMARY KEY (review_id, order_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_reviews_order ON fact_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_fact_reviews_score ON fact_reviews(review_score);
CREATE INDEX IF NOT EXISTS idx_fact_reviews_sentiment ON fact_reviews(sentiment);

-- 5. FACT_DELIVERY (Grain: 1 row per delivered order with SLA metrics)
CREATE TABLE IF NOT EXISTS fact_delivery (
    order_id VARCHAR(32) PRIMARY KEY REFERENCES fact_orders(order_id),
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ NOT NULL,
    order_estimated_delivery_date TIMESTAMPTZ NOT NULL,
    delivery_duration_days NUMERIC(8,2) NOT NULL,
    carrier_delivery_days NUMERIC(8,2),
    delivery_delay_days NUMERIC(8,2) NOT NULL,
    is_on_time INT NOT NULL CHECK (is_on_time IN (0, 1)),
    is_late INT NOT NULL CHECK (is_late IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_fact_delivery_on_time ON fact_delivery(is_on_time);
CREATE INDEX IF NOT EXISTS idx_fact_delivery_duration ON fact_delivery(delivery_duration_days);
