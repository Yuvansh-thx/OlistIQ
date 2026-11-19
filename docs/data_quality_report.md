# OlistIQ Comprehensive Data Quality & Cleaning Audit Report

- **Audit Execution Timestamp**: `2026-11-19T16:03:48.477671+00:00`
- **Datasets Examined**: 9 Relational Source Files

## 1. Primary Key Uniqueness & Table Integrity

| Table | Primary Key | Total Rows | Exact Duplicates | PK Duplicates | PK Duplicate % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `orders` | `order_id` | 99,441 | 0 | 0 | 0.0% |
| `customers` | `customer_id` | 99,441 | 0 | 0 | 0.0% |
| `products` | `product_id` | 32,951 | 0 | 0 | 0.0% |
| `sellers` | `seller_id` | 3,095 | 0 | 0 | 0.0% |
| `order_items` | `order_id+order_item_id` | 112,650 | 0 | 0 | 0.0% |
| `payments` | `order_id+payment_sequential` | 103,886 | 0 | 0 | 0.0% |
| `reviews` | `review_id` | 99,224 | 0 | 814 | 0.8204% |

## 2. Referential Integrity Matrix

| Relationship | Foreign Key Check | Orphan Records | Integrity Status |
| :--- | :--- | :--- | :--- |
| `order_items -> orders` | `order_id` in orders | 0 | Valid (100%) |
| `order_items -> products` | `product_id` in products | 0 | Valid (100%) |
| `order_items -> sellers` | `seller_id` in sellers | 0 | Valid (100%) |
| `orders -> customers` | `customer_id` in customers | 0 | Valid (100%) |
| `payments -> orders` | `order_id` in orders | 0 | Valid (100%) |
| `reviews -> orders` | `order_id` in orders | 0 | Valid (100%) |

## 3. Business Rule & Anomaly Audits

### Temporal Integrity (Orders)
- **Invalid Purchase Dates**: `0`
- **Delivered Before Purchase**: `0`
- **Carrier Before Purchase**: `166`
- **Approved Significantly Before Purchase**: `0`
- **Delivered Status Missing Delivery Date**: `8`
- **Delivered With Valid Date**: `96,470`

### Numerical Integrity (Values)
- **Negative Prices**: `0`
- **Zero Prices**: `0`
- **Negative Freight**: `0`
- **Zero Freight**: `383`
- **Negative Payments**: `0`
- **Zero Payments**: `9`

### Geolocation Integrity (Coordinates)
- **Total Raw Rows**: `1,000,163`
- **Unique Zip Prefixes**: `19,015`
- **Lat Outliers Outside Brazil**: `31`
- **Lng Outliers Outside Brazil**: `37`
- **Outlier Percentage**: `0.007`

## 4. Formal Cleaning Action Plan & Decision Matrix

### Geolocation Table Redundancy (1,000,163 rows with high coordinate variance per zip code)
- **Frequency**: 1,000,163 rows across 19,015 unique zip codes
- **Business Impact**: Consumes ~60MB alone, threatening Supabase 500MB free-tier storage.
- **Treatment Strategy**: Filter out coordinates outside Brazil bounding box, aggregate by 'geolocation_zip_code_prefix' to compute median lat/long centroid and dominant city/state.
- **Final Engineering Decision**: Deduplicate and aggregate into clean dim_geography (~19,013 rows, ~1.8MB, 97% reduction).

### Product Category Translations & Missing English Names
- **Frequency**: 610 products without category name
- **Business Impact**: Uncategorized sales degrade category revenue analytics and BI dashboards.
- **Treatment Strategy**: Map Portuguese category names to English using translation dataset; impute missing values as 'unknown_category'.
- **Final Engineering Decision**: Provide standardized English category hierarchy with 'unknown_category' for complete coverage.

### Review Record Duplicates on review_id
- **Frequency**: 814 duplicate review_ids across 99,224 reviews
- **Business Impact**: Potential double-counting of CSAT scores and review metrics in BI aggregations.
- **Treatment Strategy**: Deduplicate reviews on (review_id, order_id) and keep the latest review_creation_date / review_answer_timestamp.
- **Final Engineering Decision**: Ensure grain of 1 review per (order_id, review_id) composite key.

### Orders with non-delivered statuses or missing delivered timestamps
- **Frequency**: 8 delivered orders missing customer delivery timestamp; 8 order statuses present
- **Business Impact**: Skewed logistics delivery SLA metrics if non-delivered or cancelled orders are included.
- **Treatment Strategy**: Flag delivery SLA calculations to strictly include status == 'delivered' and non-null customer delivery timestamps.
- **Final Engineering Decision**: Preserve all orders in fact_orders; isolate on-time delivery metrics to completed deliveries with explicit denominator documentation.

### Zero Payment Value Transactions
- **Frequency**: 9 payment records with 0.0 value
- **Business Impact**: Represents promo voucher coverage or zero-cost gift transactions.
- **Treatment Strategy**: Preserve records in payment facts with voucher payment_type flag, preventing division by zero.
- **Final Engineering Decision**: Do not delete; tag appropriately in dimensional payment analysis.

