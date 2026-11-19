# OlistIQ Google Looker Studio Deployment & Configuration Guide

This guide provides the exact steps to connect Looker Studio to Supabase PostgreSQL or standardized CSV extracts and reproduce the 6 portfolio dashboards.

## 1. Connecting Data Sources

### Option A: Direct Supabase PostgreSQL Connection (Live Database)
1. Open [Google Looker Studio](https://lookerstudio.google.com/) and click **Create** > **Data Source**.
2. Select the **PostgreSQL** connector.
3. Enter your Supabase connection parameters:
   - **Host**: `aws-0-[region].pooler.supabase.com` (from `.env`)
   - **Port**: `6543` (Transaction pooler) or `5432`
   - **Database**: `postgres`
   - **Username**: `postgres.[your-project-ref]`
   - **Password**: `[your-supabase-db-password]`
   - Check **Enable SSL**.
4. Under **Table**, select the pre-aggregated analytical view: `bi_monthly_sales` (or `bi_executive_overview`).

### Option B: Standardized CSV Upload (Zero Configuration)
1. Upload the pre-generated exports located in `data/exports/`:
   - `bi_monthly_sales.csv`
   - `bi_category_performance.csv`
   - `bi_delivery_performance.csv`
   - `bi_customer_segments.csv`
   - `bi_customer_reviews.csv`

## 2. Dashboard Creation Specifications

### 1. Executive Overview Dashboard
- **Data Source Binding**: `Supabase View: bi_executive_overview / bi_monthly_sales`
- **Scorecard KPIs**:
  - **Gross Merchandise Value**: `SUM(total_gmv)` (Currency (BRL))
  - **Total Orders**: `SUM(total_orders)` (Number)
  - **Average Order Value**: `SUM(total_gmv)/SUM(total_orders)` (Currency (BRL))
  - **On-Time Delivery Rate**: `SUM(on_time_deliveries)/SUM(total_delivered_orders)` (Percent)
- **Visual Components**:
  - **Monthly GMV & Order Velocity Trend** (`Time Series Line & Area Chart`): Dimension = `year_month`, Metric = `['SUM(total_gmv)', 'SUM(total_orders)']`
  - **Top Categories Revenue Distribution** (`Donut Chart`): Dimension = `category`, Metric = `SUM(category_gmv)`
  - **Brazilian Regional Sales Concentration** (`Geo Map`): Dimension = `customer_state`, Metric = `SUM(total_delivered_orders)`

### 2. Sales Intelligence Dashboard
- **Data Source Binding**: `Supabase View: bi_monthly_sales`
- **Scorecard KPIs**:
  - **Product Sales (Net)**: `SUM(total_product_sales)` (Currency (BRL))
  - **Freight Revenue**: `SUM(total_freight_revenue)` (Currency (BRL))
  - **Units Sold**: `SUM(total_units_sold)` (Number)
- **Visual Components**:
  - **Product Sales vs Freight Revenue by Month** (`Stacked Bar Chart`): Dimension = `year_month`, Metric = `['SUM(total_product_sales)', 'SUM(total_freight_revenue)']`
  - **Monthly Performance Breakdown** (`Table with Heatmap`): Dimension = `year_month`, Metric = `['total_orders', 'total_gmv', 'average_order_value', 'mom_gmv_growth_pct']`

### 3. Customer Intelligence Dashboard
- **Data Source Binding**: `Extract: bi_customer_segments.csv / bi_customer_cohorts.csv`
- **Scorecard KPIs**:
  - **Total Unique Buyers**: `COUNT_DISTINCT(customer_unique_id)` (Number)
  - **Repeat Buyer Rate**: `3.06%` (Percent)
  - **Projected CLV**: `R$ 48.74` (Currency (BRL))
- **Visual Components**:
  - **Customer Count by RFM Segment** (`Bar Chart`): Dimension = `rfm_segment`, Metric = `COUNT(customer_unique_id)`
  - **Cohort Retention Matrix (% of Initial Month)** (`Pivot Table`): Dimension = `N/A`, Metric = `AVG(retention_rate)`

### 4. Logistics & SLA Intelligence Dashboard
- **Data Source Binding**: `Supabase View: bi_delivery_performance`
- **Scorecard KPIs**:
  - **On-Time Delivery Rate**: `91.89%` (Percent)
  - **Average Delivery Duration**: `12.56 Days` (Number)
  - **Average Days Ahead of SLA**: `13.01 Days` (Number)
- **Visual Components**:
  - **Average Delivery Days by Customer State** (`Horizontal Bar Chart`): Dimension = `customer_state`, Metric = `AVG(avg_delivery_duration_days)`
  - **Delivery Duration vs Late Breach Rate by Region** (`Scatter Plot`): Dimension = `customer_state`, Metric = `N/A`

### 5. Product & Seller Intelligence Dashboard
- **Data Source Binding**: `Supabase View: bi_category_performance / bi_seller_performance`
- **Scorecard KPIs**:
  - **Active Product Categories**: `72` (Number)
  - **Active Marketplace Sellers**: `3,095` (Number)
  - **Average Selling Price**: `R$ 120.65` (Currency (BRL))
- **Visual Components**:
  - **Top 15 Categories by GMV Contribution** (`Bar Chart`): Dimension = `category`, Metric = `SUM(category_gmv)`
  - **Top Marketplace Sellers Leaderboard** (`Table with Bars`): Dimension = `seller_id`, Metric = `['total_seller_gmv', 'total_orders', 'avg_seller_review_score', 'seller_state']`

### 6. Customer Experience & CSAT Dashboard
- **Data Source Binding**: `Supabase View: bi_customer_reviews`
- **Scorecard KPIs**:
  - **Average Review CSAT**: `4.09 / 5.0` (Rating)
  - **Promoter Share (4-5 Stars)**: `76.8%` (Percent)
  - **Detractor Share (1-2 Stars)**: `14.7%` (Percent)
- **Visual Components**:
  - **Rating Score Distribution (1 to 5 Stars)** (`Column Chart`): Dimension = `review_score`, Metric = `SUM(total_reviews)`
  - **CSAT Drop for On-Time vs Late Deliveries** (`Bar Chart`): Dimension = `Delivery Status`, Metric = `Average CSAT`

