# OlistIQ Dataset Inventory & Raw Validation Report

- **Dataset Source**: `olistbr/brazilian-ecommerce` (Kaggle)
- **Download Timestamp (UTC)**: `2026-11-19T16:13:46.642134+00:00`
- **Source Cache**: `/Users/shivanshyadav/.cache/kagglehub/datasets/olistbr/brazilian-ecommerce/versions/2`
- **Local Raw Target**: `/Users/shivanshyadav/Desktop/Data Analytics Project/OSlit/data/raw`
- **Validated Expected Files**: 9 / 9

## File Summaries

| File Name | Rows | Columns | Size (MB) | Total Missing Values |
| :--- | :--- | :--- | :--- | :--- |
| `olist_orders_dataset.csv` | 99,441 | 8 | 16.84 MB | 4,908 |
| `olist_order_items_dataset.csv` | 112,650 | 7 | 14.72 MB | 0 |
| `olist_customers_dataset.csv` | 99,441 | 5 | 8.62 MB | 0 |
| `olist_products_dataset.csv` | 32,951 | 9 | 2.27 MB | 2,448 |
| `olist_order_payments_dataset.csv` | 103,886 | 5 | 5.51 MB | 0 |
| `olist_order_reviews_dataset.csv` | 99,224 | 7 | 13.78 MB | 145,903 |
| `olist_sellers_dataset.csv` | 3,095 | 4 | 0.17 MB | 0 |
| `product_category_name_translation.csv` | 71 | 2 | 0.0 MB | 0 |
| `olist_geolocation_dataset.csv` | 1,000,163 | 5 | 58.44 MB | 0 |

## Detailed Schema & Null Profile

### `olist_orders_dataset.csv`
Rows: **99,441** | Columns: **8** | Size: **16.84 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0 | 0.0% |
| `customer_id` | `str` | 0 | 0.0% |
| `order_status` | `str` | 0 | 0.0% |
| `order_purchase_timestamp` | `str` | 0 | 0.0% |
| `order_approved_at` | `str` | 160 | 0.16% |
| `order_delivered_carrier_date` | `str` | 1,783 | 1.79% |
| `order_delivered_customer_date` | `str` | 2,965 | 2.98% |
| `order_estimated_delivery_date` | `str` | 0 | 0.0% |

### `olist_order_items_dataset.csv`
Rows: **112,650** | Columns: **7** | Size: **14.72 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0 | 0.0% |
| `order_item_id` | `int64` | 0 | 0.0% |
| `product_id` | `str` | 0 | 0.0% |
| `seller_id` | `str` | 0 | 0.0% |
| `shipping_limit_date` | `str` | 0 | 0.0% |
| `price` | `float64` | 0 | 0.0% |
| `freight_value` | `float64` | 0 | 0.0% |

### `olist_customers_dataset.csv`
Rows: **99,441** | Columns: **5** | Size: **8.62 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `customer_id` | `str` | 0 | 0.0% |
| `customer_unique_id` | `str` | 0 | 0.0% |
| `customer_zip_code_prefix` | `int64` | 0 | 0.0% |
| `customer_city` | `str` | 0 | 0.0% |
| `customer_state` | `str` | 0 | 0.0% |

### `olist_products_dataset.csv`
Rows: **32,951** | Columns: **9** | Size: **2.27 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `product_id` | `str` | 0 | 0.0% |
| `product_category_name` | `str` | 610 | 1.85% |
| `product_name_lenght` | `float64` | 610 | 1.85% |
| `product_description_lenght` | `float64` | 610 | 1.85% |
| `product_photos_qty` | `float64` | 610 | 1.85% |
| `product_weight_g` | `float64` | 2 | 0.01% |
| `product_length_cm` | `float64` | 2 | 0.01% |
| `product_height_cm` | `float64` | 2 | 0.01% |
| `product_width_cm` | `float64` | 2 | 0.01% |

### `olist_order_payments_dataset.csv`
Rows: **103,886** | Columns: **5** | Size: **5.51 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0 | 0.0% |
| `payment_sequential` | `int64` | 0 | 0.0% |
| `payment_type` | `str` | 0 | 0.0% |
| `payment_installments` | `int64` | 0 | 0.0% |
| `payment_value` | `float64` | 0 | 0.0% |

### `olist_order_reviews_dataset.csv`
Rows: **99,224** | Columns: **7** | Size: **13.78 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `review_id` | `str` | 0 | 0.0% |
| `order_id` | `str` | 0 | 0.0% |
| `review_score` | `int64` | 0 | 0.0% |
| `review_comment_title` | `str` | 87,656 | 88.34% |
| `review_comment_message` | `str` | 58,247 | 58.7% |
| `review_creation_date` | `str` | 0 | 0.0% |
| `review_answer_timestamp` | `str` | 0 | 0.0% |

### `olist_sellers_dataset.csv`
Rows: **3,095** | Columns: **4** | Size: **0.17 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `seller_id` | `str` | 0 | 0.0% |
| `seller_zip_code_prefix` | `int64` | 0 | 0.0% |
| `seller_city` | `str` | 0 | 0.0% |
| `seller_state` | `str` | 0 | 0.0% |

### `product_category_name_translation.csv`
Rows: **71** | Columns: **2** | Size: **0.0 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `product_category_name` | `str` | 0 | 0.0% |
| `product_category_name_english` | `str` | 0 | 0.0% |

### `olist_geolocation_dataset.csv`
Rows: **1,000,163** | Columns: **5** | Size: **58.44 MB**

| Column | Inferred Dtype | Missing Count | Null % |
| :--- | :--- | :--- | :--- |
| `geolocation_zip_code_prefix` | `int64` | 0 | 0.0% |
| `geolocation_lat` | `float64` | 0 | 0.0% |
| `geolocation_lng` | `float64` | 0 | 0.0% |
| `geolocation_city` | `str` | 0 | 0.0% |
| `geolocation_state` | `str` | 0 | 0.0% |

