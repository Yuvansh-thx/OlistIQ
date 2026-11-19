# OlistIQ Central KPI Dictionary & Metric Governance Standard

This document establishes the authoritative definitions, mathematical formulations, SQL/DAX implementations, aggregation grains, and analytical constraints for all key performance indicators across Python, PostgreSQL/Supabase, Power BI, Tableau, and Google Looker Studio.

---

## 1. Gross Merchandise Value (GMV)
* **Definition**: Total monetary value of merchandise sold on the platform, inclusive of product price and freight charges, excluding canceled orders.
* **Formula**: $\sum (\text{price} + \text{freight\_value})$ for all orders where $\text{order\_status} \neq \text{'canceled'}$
* **Aggregation Grain**: Order Item level (`fact_order_items`) filtered by Order status (`fact_orders`).
* **SQL Implementation**:
  ```sql
  SELECT SUM(foi.total_item_value) AS gmv
  FROM fact_order_items foi
  JOIN fact_orders fo ON foi.order_id = fo.order_id
  WHERE fo.order_status <> 'canceled';
  ```
* **Python Implementation**:
  ```python
  gmv = float(valid_items["total_item_value"].sum())
  ```
* **DAX Implementation**:
  ```dax
  GMV = CALCULATE(
      SUM(fact_order_items[total_item_value]),
      fact_orders[order_status] <> "canceled"
  )
  ```
* **Business Interpretation**: The top-line sales throughput metric measuring the scale of the marketplace.
* **Known Limitations & Anti-Patterns**: Never calculate GMV by summing `fact_payments[payment_value]`, which reflects settled financial receipts (including vouchers and installment credit surcharges), nor by joining `fact_orders` directly with multiple tables without pre-aggregating, which causes Cartesian join multiplication.

---

## 2. Total Completed Orders
* **Definition**: Distinct count of orders that successfully entered the fulfillment pipeline (delivered, shipped, invoiced, processing, approved).
* **Formula**: $\text{CountDistinct}(\text{order\_id})$ where $\text{order\_status} \neq \text{'canceled'}$
* **Aggregation Grain**: Order level (`fact_orders`).
* **SQL Implementation**:
  ```sql
  SELECT COUNT(DISTINCT order_id) AS total_orders
  FROM fact_orders
  WHERE order_status <> 'canceled';
  ```
* **DAX Implementation**:
  ```dax
  Total Orders = CALCULATE(
      DISTINCTCOUNT(fact_orders[order_id]),
      fact_orders[order_status] <> "canceled"
  )
  ```
* **Business Interpretation**: Volume indicator of order generation.
* **Known Limitations**: Canceled orders (~625 records) are excluded to ensure operational accuracy.

---

## 3. Average Order Value (AOV)
* **Definition**: Average gross merchandise spend generated per non-canceled order.
* **Formula**: $\frac{\text{GMV}}{\text{Total Completed Orders}}$
* **Aggregation Grain**: Order level.
* **SQL Implementation**:
  ```sql
  SELECT ROUND(SUM(foi.total_item_value) / COUNT(DISTINCT fo.order_id), 2) AS aov
  FROM fact_order_items foi
  JOIN fact_orders fo ON foi.order_id = fo.order_id
  WHERE fo.order_status <> 'canceled';
  ```
* **DAX Implementation**:
  ```dax
  AOV = DIVIDE([GMV], [Total Orders], 0)
  ```
* **Business Interpretation**: Measures customer basket size and willingness to spend per checkout transaction.

---

## 4. Repeat Purchase Rate
* **Definition**: Percentage of unique customers who have made more than one completed order across their historical lifetime.
* **Formula**: $\frac{\text{Count}(\text{Customers with Orders} > 1)}{\text{Total Unique Customers}} \times 100$
* **Aggregation Grain**: Customer Unique ID level (`dim_customers.customer_unique_id`).
* **SQL Implementation**:
  ```sql
  WITH cust_orders AS (
      SELECT dc.customer_unique_id, COUNT(DISTINCT fo.order_id) AS orders_count
      FROM dim_customers dc
      JOIN fact_orders fo ON dc.customer_id = fo.customer_id
      WHERE fo.order_status <> 'canceled'
      GROUP BY dc.customer_unique_id
  )
  SELECT ROUND(SUM(CASE WHEN orders_count > 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS repeat_rate
  FROM cust_orders;
  ```
* **Business Interpretation**: Indicator of customer retention and marketplace loyalty.
* **Known Limitations**: Olist is an aggregation marketplace with an observed repeat purchase rate of ~3.06%, reflecting a predominantly acquisition-driven funnel during this period.

---

## 5. On-Time Delivery Rate
* **Definition**: Percentage of completed deliveries where the customer delivery timestamp was on or before the estimated delivery timestamp.
* **Formula**: $\frac{\text{Count}(\text{Orders with } \text{delivered\_date} \leq \text{estimated\_date})}{\text{Total Delivered Orders with Delivery Date}} \times 100$
* **Aggregation Grain**: Delivered Order level (`fact_delivery`).
* **SQL Implementation**:
  ```sql
  SELECT ROUND(SUM(is_on_time) * 100.0 / COUNT(order_id), 2) AS on_time_delivery_rate_pct
  FROM fact_delivery;
  ```
* **DAX Implementation**:
  ```dax
  On-Time Delivery Rate = DIVIDE(
      CALCULATE(COUNTROWS(fact_delivery), fact_delivery[is_on_time] = 1),
      COUNTROWS(fact_delivery),
      0
  ) * 100
  ```
* **Business Interpretation**: Operational efficiency and carrier SLA fulfillment compliance.
* **Known Limitations**: The denominator strictly consists of 96,470 orders with recorded customer delivery dates; orders currently in transit or canceled are excluded.

---

## 6. Average Review Score (CSAT)
* **Definition**: Arithmetic mean of the customer rating score (1 to 5 stars) provided on post-order survey reviews.
* **Formula**: $\frac{\sum \text{review\_score}}{\text{Total Reviews}}$
* **Aggregation Grain**: Review level (`fact_reviews`).
* **SQL Implementation**:
  ```sql
  SELECT ROUND(AVG(review_score), 2) AS average_csat
  FROM fact_reviews;
  ```
* **DAX Implementation**:
  ```dax
  Average CSAT = AVERAGE(fact_reviews[review_score])
  ```
* **Business Interpretation**: Direct measure of customer satisfaction and platform brand perception.

---

## 7. Month-over-Month (MoM) GMV Growth %
* **Definition**: Percentage change in Gross Merchandise Value comparing month $M$ against month $M-1$.
* **Formula**: $\frac{\text{GMV}_t - \text{GMV}_{t-1}}{\text{GMV}_{t-1}} \times 100$
* **Aggregation Grain**: Monthly Calendar level.
* **SQL Implementation**:
  ```sql
  SELECT 
      year_month,
      ROUND((monthly_gmv - LAG(monthly_gmv, 1) OVER (ORDER BY year_month)) * 100.0 / 
      NULLIF(LAG(monthly_gmv, 1) OVER (ORDER BY year_month), 0), 2) AS mom_gmv_growth_pct
  FROM monthly_summary;
  ```
* **DAX Implementation**:
  ```dax
  MoM GMV Growth % = 
  VAR CurrentGMV = [GMV]
  VAR PreviousGMV = CALCULATE([GMV], DATEADD(dim_date[full_date], -1, MONTH))
  RETURN DIVIDE(CurrentGMV - PreviousGMV, PreviousGMV, 0) * 100
  ```
