# OlistIQ — Data Dictionary & Entity Definitions

## 1. `dim_customers`
| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `customer_id` | VARCHAR(32) | No | Primary Key. Specific order customer token. |
| `customer_unique_id` | VARCHAR(32) | No | Identifier representing the unique physical buyer across multiple orders. |
| `city` | VARCHAR(100) | Yes | Customer residence city. |
| `state` | VARCHAR(5) | Yes | Brazilian state federation code (e.g. SP, RJ, MG). |
| `zip_code_prefix` | INT | Yes | 5-digit postal code prefix. |

## 2. `dim_products`
| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `product_id` | VARCHAR(32) | No | Primary Key. Unique product alphanumeric identifier. |
| `category_name_portuguese` | VARCHAR(100) | No | Original Portuguese category name. |
| `category_name_english` | VARCHAR(100) | No | Mapped standardized English category. |
| `category_display_name` | VARCHAR(100) | No | Clean Title Case display category name. |
| `weight_g` | NUMERIC(10,1) | Yes | Physical product weight in grams. |

## 3. `fact_orders`
| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | VARCHAR(32) | No | Primary Key. Distinct purchase transaction code. |
| `customer_id` | VARCHAR(32) | No | Foreign key referencing `dim_customers`. |
| `order_status` | VARCHAR(25) | No | Lifecycle status (delivered, shipped, canceled, invoiced, etc.). |
| `order_purchase_timestamp` | TIMESTAMPTZ | No | Timestamp of order creation. |
| `order_delivered_customer_date`| TIMESTAMPTZ | Yes | Actual timestamp of customer receipt. |
| `order_estimated_delivery_date`| TIMESTAMPTZ | No | Quoted delivery promise date. |

## 4. `fact_order_items`
| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | VARCHAR(32) | No | Part of composite PK. Reference to `fact_orders`. |
| `order_item_id` | INT | No | Sequential item line number within the order. |
| `product_id` | VARCHAR(32) | No | Foreign key referencing `dim_products`. |
| `seller_id` | VARCHAR(32) | No | Foreign key referencing `dim_sellers`. |
| `price` | NUMERIC(10,2) | No | Product item sales price in BRL. |
| `freight_value` | NUMERIC(10,2) | No | Shipping charge allocated to this item in BRL. |
| `total_item_value`| NUMERIC(10,2) | No | Computed GMV contribution (`price + freight_value`). |
