-- ============================================================================
-- OlistIQ PostgreSQL Schema Migration: 01_create_dimensions.sql
-- Star Schema Dimension Tables
-- ============================================================================

-- 1. DIM_DATE
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter INT NOT NULL,
    year_quarter VARCHAR(10) NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    week_of_year INT NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    is_weekend INT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_date_year_month ON dim_date(year_month);
CREATE INDEX IF NOT EXISTS idx_dim_date_full_date ON dim_date(full_date);

-- 2. DIM_GEOGRAPHY (Aggregated Zip Code Centroids)
CREATE TABLE IF NOT EXISTS dim_geography (
    zip_code_prefix INT PRIMARY KEY,
    latitude NUMERIC(8,4) NOT NULL,
    longitude NUMERIC(8,4) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(5) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_geo_state ON dim_geography(state);
CREATE INDEX IF NOT EXISTS idx_dim_geo_city ON dim_geography(city);

-- 3. DIM_CUSTOMERS
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    zip_code_prefix INT,
    city VARCHAR(100),
    state VARCHAR(5)
);

CREATE INDEX IF NOT EXISTS idx_dim_customers_unique_id ON dim_customers(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_dim_customers_state ON dim_customers(state);

-- 4. DIM_PRODUCTS
CREATE TABLE IF NOT EXISTS dim_products (
    product_id VARCHAR(32) PRIMARY KEY,
    category_name_portuguese VARCHAR(100),
    category_name_english VARCHAR(100) NOT NULL,
    category_display_name VARCHAR(100) NOT NULL,
    name_length NUMERIC(6,1),
    description_length NUMERIC(8,1),
    photos_qty NUMERIC(4,1),
    weight_g NUMERIC(10,1),
    length_cm NUMERIC(6,1),
    height_cm NUMERIC(6,1),
    width_cm NUMERIC(6,1)
);

CREATE INDEX IF NOT EXISTS idx_dim_products_category ON dim_products(category_name_english);

-- 5. DIM_SELLERS
CREATE TABLE IF NOT EXISTS dim_sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    zip_code_prefix INT,
    city VARCHAR(100),
    state VARCHAR(5)
);

CREATE INDEX IF NOT EXISTS idx_dim_sellers_state ON dim_sellers(state);

-- 6. DIM_PAYMENT_TYPES
CREATE TABLE IF NOT EXISTS dim_payment_types (
    payment_type_id SERIAL PRIMARY KEY,
    payment_type_name VARCHAR(50) NOT NULL UNIQUE
);
