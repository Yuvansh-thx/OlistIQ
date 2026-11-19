# OlistIQ Power BI DAX Measures & Tabular Catalog

| Measure Name | DAX Expression | Format | Business Definition |
| :--- | :--- | :--- | :--- |
| **`GMV`** | `CALCULATE(SUM('fact_order_items'[total_item_value]), 'fact_orders'[order_status] <> "canceled")` | `R$ #,##0.00` | Gross Merchandise Value inclusive of freight, excluding canceled orders. |
| **`Product Sales`** | `CALCULATE(SUM('fact_order_items'[price]), 'fact_orders'[order_status] <> "canceled")` | `R$ #,##0.00` | Total merchandise sales value excluding freight charges. |
| **`Freight Revenue`** | `CALCULATE(SUM('fact_order_items'[freight_value]), 'fact_orders'[order_status] <> "canceled")` | `R$ #,##0.00` | Total logistics and freight charges collected. |
| **`Total Orders`** | `CALCULATE(DISTINCTCOUNT('fact_orders'[order_id]), 'fact_orders'[order_status] <> "canceled")` | `#,##0` | Total number of completed or processing orders. |
| **`Units Sold`** | `COUNTROWS('fact_order_items')` | `#,##0` | Total number of physical items ordered. |
| **`AOV`** | `DIVIDE([GMV], [Total Orders], 0)` | `R$ #,##0.00` | Average Order Value generated per order. |
| **`Average Item Price`** | `DIVIDE([Product Sales], [Units Sold], 0)` | `R$ #,##0.00` | Average selling price per unit. |
| **`Total Unique Customers`** | `DISTINCTCOUNT('dim_customers'[customer_unique_id])` | `#,##0` | Unique individual buyers registered across history. |
| **`Repeat Buyers`** | `COUNTROWS(FILTER(VALUES('dim_customers'[customer_unique_id]), CALCULATE([Total Orders]) > 1))` | `#,##0` | Customers who completed 2 or more distinct orders. |
| **`Repeat Purchase Rate %`** | `DIVIDE([Repeat Buyers], [Total Unique Customers], 0) * 100` | `0.00"%"` | Percentage of unique customer base with repeated transactions. |
| **`On-Time Delivery Rate %`** | `DIVIDE(CALCULATE(COUNTROWS('fact_delivery'), 'fact_delivery'[is_on_time] = 1), COUNTROWS('fact_delivery'), 0) * 100` | `0.00"%"` | Percentage of delivered orders delivered on or ahead of estimated SLA. |
| **`Average Delivery Duration Days`** | `AVERAGE('fact_delivery'[delivery_duration_days])` | `0.0" days"` | Average elapsed business days from purchase to customer doorstep receipt. |
| **`Average Delivery Delay Days`** | `CALCULATE(AVERAGE('fact_delivery'[delivery_delay_days]), 'fact_delivery'[is_late] = 1)` | `0.0" days"` | Average days late for orders breaching expected delivery date. |
| **`Average CSAT`** | `AVERAGE('fact_reviews'[review_score])` | `0.00` | Average review score rating across all collected customer evaluations. |
| **`Negative Review Rate %`** | `DIVIDE(CALCULATE(COUNTROWS('fact_reviews'), 'fact_reviews'[review_score] IN {1, 2}), COUNTROWS('fact_reviews'), 0) * 100` | `0.00"%"` | Percentage of customer reviews rated 1 or 2 stars. |
| **`Promoter Review Rate %`** | `DIVIDE(CALCULATE(COUNTROWS('fact_reviews'), 'fact_reviews'[review_score] IN {4, 5}), COUNTROWS('fact_reviews'), 0) * 100` | `0.00"%"` | Percentage of customer reviews rated 4 or 5 stars. |
| **`MoM GMV Growth %`** | `VAR CurrentGMV = [GMV] VAR PriorGMV = CALCULATE([GMV], DATEADD('dim_date'[full_date], -1, MONTH)) RETURN DIVIDE(CurrentGMV - PriorGMV, PriorGMV, 0) * 100` | `0.00"%"` | Month-over-month Gross Merchandise Value growth percentage. |

## Tabular Star Schema Relationships

| Relationship | From Table | From Column | To Table | To Column | Cardinality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Rel_Orders_Customers` | `fact_orders` | `customer_id` | `dim_customers` | `customer_id` | Many-to-One (*:1) |
| `Rel_OrderItems_Orders` | `fact_order_items` | `order_id` | `fact_orders` | `order_id` | Many-to-One (*:1) |
| `Rel_OrderItems_Products` | `fact_order_items` | `product_id` | `dim_products` | `product_id` | Many-to-One (*:1) |
| `Rel_OrderItems_Sellers` | `fact_order_items` | `seller_id` | `dim_sellers` | `seller_id` | Many-to-One (*:1) |
| `Rel_Orders_Date` | `fact_orders` | `purchase_date_key` | `dim_date` | `date_key` | Many-to-One (*:1) |
| `Rel_Payments_Orders` | `fact_payments` | `order_id` | `fact_orders` | `order_id` | Many-to-One (*:1) |
| `Rel_Reviews_Orders` | `fact_reviews` | `order_id` | `fact_orders` | `order_id` | Many-to-One (*:1) |
| `Rel_Delivery_Orders` | `fact_delivery` | `order_id` | `fact_orders` | `order_id` | Many-to-One (*:1) |
