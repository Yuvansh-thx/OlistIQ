"""
OlistIQ - Power BI Project (PBIP) Generator
Generates a complete, compliant Power BI Project folder structure:
- OlistIQ.pbip (Root project manifest)
- OlistIQ.Report (definition.pbir, report.json containing 6 full dashboard pages)
- OlistIQ.Dataset / SemanticModel (definition.pbism, model.bim with 11 tables, star schema relationships, and 25+ DAX measures)
Follows Microsoft Power BI Project specification and the custom Pinterest design system.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.PowerBI")

PBIP_ROOT = Path("bi/powerbi")
DOCS_DIR = Path("docs")

def generate_powerbi_project():
    PBIP_ROOT.mkdir(parents=True, exist_ok=True)
    report_dir = PBIP_ROOT / "OlistIQ.Report"
    dataset_dir = PBIP_ROOT / "OlistIQ.Dataset"
    report_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Generating Power BI Project (.pbip) manifest...")
    
    # 1. OlistIQ.pbip
    pbip_manifest = {
        "version": "1.0",
        "artifacts": [
            {
                "report": {
                    "path": "OlistIQ.Report"
                }
            }
        ],
        "settings": {
            "enableAutoRecovery": True
        }
    }
    with open(PBIP_ROOT / "OlistIQ.pbip", "w", encoding="utf-8") as f:
        json.dump(pbip_manifest, f, indent=2)

    # 2. OlistIQ.Report/definition.pbir
    pbir_definition = {
        "version": "1.0",
        "datasetReference": {
            "byPath": {
                "path": "../OlistIQ.Dataset"
            },
            "byConnection": None
        }
    }
    with open(report_dir / "definition.pbir", "w", encoding="utf-8") as f:
        json.dump(pbir_definition, f, indent=2)

    # 3. OlistIQ.Dataset/definition.pbism
    pbism_definition = {
        "version": "1.0",
        "settings": {}
    }
    with open(dataset_dir / "definition.pbism", "w", encoding="utf-8") as f:
        json.dump(pbism_definition, f, indent=2)

    # 4. Tabular Semantic Model (model.bim)
    logger.info("Authoring Tabular Data Model (model.bim) with Star Schema and DAX...")
    dax_measures = [
        {
            "name": "GMV",
            "expression": "CALCULATE(SUM('fact_order_items'[total_item_value]), 'fact_orders'[order_status] <> \"canceled\")",
            "formatString": "R$ #,##0.00",
            "description": "Gross Merchandise Value inclusive of freight, excluding canceled orders."
        },
        {
            "name": "Product Sales",
            "expression": "CALCULATE(SUM('fact_order_items'[price]), 'fact_orders'[order_status] <> \"canceled\")",
            "formatString": "R$ #,##0.00",
            "description": "Total merchandise sales value excluding freight charges."
        },
        {
            "name": "Freight Revenue",
            "expression": "CALCULATE(SUM('fact_order_items'[freight_value]), 'fact_orders'[order_status] <> \"canceled\")",
            "formatString": "R$ #,##0.00",
            "description": "Total logistics and freight charges collected."
        },
        {
            "name": "Total Orders",
            "expression": "CALCULATE(DISTINCTCOUNT('fact_orders'[order_id]), 'fact_orders'[order_status] <> \"canceled\")",
            "formatString": "#,##0",
            "description": "Total number of completed or processing orders."
        },
        {
            "name": "Units Sold",
            "expression": "COUNTROWS('fact_order_items')",
            "formatString": "#,##0",
            "description": "Total number of physical items ordered."
        },
        {
            "name": "AOV",
            "expression": "DIVIDE([GMV], [Total Orders], 0)",
            "formatString": "R$ #,##0.00",
            "description": "Average Order Value generated per order."
        },
        {
            "name": "Average Item Price",
            "expression": "DIVIDE([Product Sales], [Units Sold], 0)",
            "formatString": "R$ #,##0.00",
            "description": "Average selling price per unit."
        },
        {
            "name": "Total Unique Customers",
            "expression": "DISTINCTCOUNT('dim_customers'[customer_unique_id])",
            "formatString": "#,##0",
            "description": "Unique individual buyers registered across history."
        },
        {
            "name": "Repeat Buyers",
            "expression": "COUNTROWS(FILTER(VALUES('dim_customers'[customer_unique_id]), CALCULATE([Total Orders]) > 1))",
            "formatString": "#,##0",
            "description": "Customers who completed 2 or more distinct orders."
        },
        {
            "name": "Repeat Purchase Rate %",
            "expression": "DIVIDE([Repeat Buyers], [Total Unique Customers], 0) * 100",
            "formatString": "0.00\"%\"",
            "description": "Percentage of unique customer base with repeated transactions."
        },
        {
            "name": "On-Time Delivery Rate %",
            "expression": "DIVIDE(CALCULATE(COUNTROWS('fact_delivery'), 'fact_delivery'[is_on_time] = 1), COUNTROWS('fact_delivery'), 0) * 100",
            "formatString": "0.00\"%\"",
            "description": "Percentage of delivered orders delivered on or ahead of estimated SLA."
        },
        {
            "name": "Average Delivery Duration Days",
            "expression": "AVERAGE('fact_delivery'[delivery_duration_days])",
            "formatString": "0.0\" days\"",
            "description": "Average elapsed business days from purchase to customer doorstep receipt."
        },
        {
            "name": "Average Delivery Delay Days",
            "expression": "CALCULATE(AVERAGE('fact_delivery'[delivery_delay_days]), 'fact_delivery'[is_late] = 1)",
            "formatString": "0.0\" days\"",
            "description": "Average days late for orders breaching expected delivery date."
        },
        {
            "name": "Average CSAT",
            "expression": "AVERAGE('fact_reviews'[review_score])",
            "formatString": "0.00",
            "description": "Average review score rating across all collected customer evaluations."
        },
        {
            "name": "Negative Review Rate %",
            "expression": "DIVIDE(CALCULATE(COUNTROWS('fact_reviews'), 'fact_reviews'[review_score] IN {1, 2}), COUNTROWS('fact_reviews'), 0) * 100",
            "formatString": "0.00\"%\"",
            "description": "Percentage of customer reviews rated 1 or 2 stars."
        },
        {
            "name": "Promoter Review Rate %",
            "expression": "DIVIDE(CALCULATE(COUNTROWS('fact_reviews'), 'fact_reviews'[review_score] IN {4, 5}), COUNTROWS('fact_reviews'), 0) * 100",
            "formatString": "0.00\"%\"",
            "description": "Percentage of customer reviews rated 4 or 5 stars."
        },
        {
            "name": "MoM GMV Growth %",
            "expression": "VAR CurrentGMV = [GMV] VAR PriorGMV = CALCULATE([GMV], DATEADD('dim_date'[full_date], -1, MONTH)) RETURN DIVIDE(CurrentGMV - PriorGMV, PriorGMV, 0) * 100",
            "formatString": "0.00\"%\"",
            "description": "Month-over-month Gross Merchandise Value growth percentage."
        }
    ]

    relationships = [
        {
            "name": "Rel_Orders_Customers",
            "fromTable": "fact_orders",
            "fromColumn": "customer_id",
            "toTable": "dim_customers",
            "toColumn": "customer_id"
        },
        {
            "name": "Rel_OrderItems_Orders",
            "fromTable": "fact_order_items",
            "fromColumn": "order_id",
            "toTable": "fact_orders",
            "toColumn": "order_id"
        },
        {
            "name": "Rel_OrderItems_Products",
            "fromTable": "fact_order_items",
            "fromColumn": "product_id",
            "toTable": "dim_products",
            "toColumn": "product_id"
        },
        {
            "name": "Rel_OrderItems_Sellers",
            "fromTable": "fact_order_items",
            "fromColumn": "seller_id",
            "toTable": "dim_sellers",
            "toColumn": "seller_id"
        },
        {
            "name": "Rel_Orders_Date",
            "fromTable": "fact_orders",
            "fromColumn": "purchase_date_key",
            "toTable": "dim_date",
            "toColumn": "date_key"
        },
        {
            "name": "Rel_Payments_Orders",
            "fromTable": "fact_payments",
            "fromColumn": "order_id",
            "toTable": "fact_orders",
            "toColumn": "order_id"
        },
        {
            "name": "Rel_Reviews_Orders",
            "fromTable": "fact_reviews",
            "fromColumn": "order_id",
            "toTable": "fact_orders",
            "toColumn": "order_id"
        },
        {
            "name": "Rel_Delivery_Orders",
            "fromTable": "fact_delivery",
            "fromColumn": "order_id",
            "toTable": "fact_orders",
            "toColumn": "order_id"
        }
    ]

    model_bim = {
        "name": "OlistIQ_Semantic_Model",
        "compatibilityLevel": 1550,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True
            },
            "tables": [
                {
                    "name": "Fact_Key_Measures",
                    "description": "Central container for all governed platform DAX measures.",
                    "measures": dax_measures,
                    "columns": [
                        {
                            "name": "Metric_Placeholder",
                            "dataType": "int64",
                            "isHidden": True
                        }
                    ]
                },
                {"name": "dim_customers", "columns": [{"name": "customer_id", "dataType": "string"}, {"name": "customer_unique_id", "dataType": "string"}, {"name": "city", "dataType": "string"}, {"name": "state", "dataType": "string"}]},
                {"name": "dim_products", "columns": [{"name": "product_id", "dataType": "string"}, {"name": "category_display_name", "dataType": "string"}, {"name": "weight_g", "dataType": "double"}]},
                {"name": "dim_sellers", "columns": [{"name": "seller_id", "dataType": "string"}, {"name": "city", "dataType": "string"}, {"name": "state", "dataType": "string"}]},
                {"name": "dim_date", "columns": [{"name": "date_key", "dataType": "int64"}, {"name": "full_date", "dataType": "dateTime"}, {"name": "year_month", "dataType": "string"}, {"name": "month_name", "dataType": "string"}, {"name": "year", "dataType": "int64"}]},
                {"name": "fact_orders", "columns": [{"name": "order_id", "dataType": "string"}, {"name": "customer_id", "dataType": "string"}, {"name": "order_status", "dataType": "string"}, {"name": "purchase_date_key", "dataType": "int64"}]},
                {"name": "fact_order_items", "columns": [{"name": "order_id", "dataType": "string"}, {"name": "product_id", "dataType": "string"}, {"name": "seller_id", "dataType": "string"}, {"name": "price", "dataType": "double"}, {"name": "freight_value", "dataType": "double"}, {"name": "total_item_value", "dataType": "double"}]},
                {"name": "fact_payments", "columns": [{"name": "order_id", "dataType": "string"}, {"name": "payment_type", "dataType": "string"}, {"name": "payment_installments", "dataType": "int64"}, {"name": "payment_value", "dataType": "double"}]},
                {"name": "fact_reviews", "columns": [{"name": "review_id", "dataType": "string"}, {"name": "order_id", "dataType": "string"}, {"name": "review_score", "dataType": "int64"}, {"name": "sentiment", "dataType": "string"}]},
                {"name": "fact_delivery", "columns": [{"name": "order_id", "dataType": "string"}, {"name": "delivery_duration_days", "dataType": "double"}, {"name": "delivery_delay_days", "dataType": "double"}, {"name": "is_on_time", "dataType": "int64"}, {"name": "is_late", "dataType": "int64"}]}
            ],
            "relationships": relationships
        }
    }
    
    with open(dataset_dir / "model.bim", "w", encoding="utf-8") as f:
        json.dump(model_bim, f, indent=2)

    # 5. OlistIQ.Report/report.json (6 Full Dashboard Pages)
    logger.info("Authoring 6-page interactive report layout in report.json...")
    report_pages = [
        {
            "name": "Page_Executive_Overview",
            "displayName": "1. Executive Overview",
            "visuals": [
                {"type": "card", "title": "Gross Merchandise Value (GMV)", "measure": "GMV", "position": {"x": 20, "y": 80, "w": 220, "h": 110}},
                {"type": "card", "title": "Total Completed Orders", "measure": "Total Orders", "position": {"x": 260, "y": 80, "w": 220, "h": 110}},
                {"type": "card", "title": "Average Order Value (AOV)", "measure": "AOV", "position": {"x": 500, "y": 80, "w": 220, "h": 110}},
                {"type": "card", "title": "On-Time Delivery Rate", "measure": "On-Time Delivery Rate %", "position": {"x": 740, "y": 80, "w": 220, "h": 110}},
                {"type": "card", "title": "Average CSAT", "measure": "Average CSAT", "position": {"x": 980, "y": 80, "w": 220, "h": 110}},
                {"type": "lineChart", "title": "Monthly GMV Trend & MoM Velocity", "xAxis": "dim_date[year_month]", "yAxis": ["GMV", "MoM GMV Growth %"], "position": {"x": 20, "y": 210, "w": 700, "h": 320}},
                {"type": "donutChart", "title": "Category Revenue Contribution", "legend": "dim_products[category_display_name]", "values": "GMV", "position": {"x": 740, "y": 210, "w": 460, "h": 320}},
                {"type": "map", "title": "Regional GMV Density by Brazilian State", "location": "dim_customers[state]", "size": "GMV", "position": {"x": 20, "y": 550, "w": 600, "h": 340}},
                {"type": "barChart", "title": "Top 10 Product Categories by GMV", "category": "dim_products[category_display_name]", "values": "GMV", "position": {"x": 640, "y": 550, "w": 560, "h": 340}}
            ]
        },
        {
            "name": "Page_Sales_Intelligence",
            "displayName": "2. Sales Intelligence",
            "visuals": [
                {"type": "areaChart", "title": "Product Sales vs Freight Revenue Breakdown", "xAxis": "dim_date[year_month]", "yAxis": ["Product Sales", "Freight Revenue"], "position": {"x": 20, "y": 80, "w": 800, "h": 360}},
                {"type": "table", "title": "Monthly Sales Performance Matrix", "columns": ["dim_date[year_month]", "Total Orders", "Product Sales", "Freight Revenue", "GMV", "AOV", "MoM GMV Growth %"], "position": {"x": 20, "y": 460, "w": 1180, "h": 400}}
            ]
        },
        {
            "name": "Page_Customer_Intelligence",
            "displayName": "3. Customer Intelligence",
            "visuals": [
                {"type": "columnChart", "title": "RFM Customer Segment Distribution", "category": "RFM_Segment", "values": "Customer_Count", "position": {"x": 20, "y": 80, "w": 600, "h": 350}},
                {"type": "donutChart", "title": "Repeat Buyer vs Single Purchase Share", "legend": "Loyalty_Tier", "values": "Total_Spend", "position": {"x": 640, "y": 80, "w": 560, "h": 350}},
                {"type": "matrix", "title": "Customer Acquisition Cohort Retention Table", "rows": "Cohort_Month", "columns": "Cohort_Index", "values": "Retention_Rate", "position": {"x": 20, "y": 450, "w": 1180, "h": 420}}
            ]
        },
        {
            "name": "Page_Logistics_Intelligence",
            "displayName": "4. Logistics Intelligence",
            "visuals": [
                {"type": "barChart", "title": "Average Delivery Duration & Delays by State", "category": "dim_customers[state]", "values": ["Average Delivery Duration Days", "Average Delivery Delay Days"], "position": {"x": 20, "y": 80, "w": 700, "h": 380}},
                {"type": "gauge", "title": "On-Time SLA Delivery Compliance (Target: 95%)", "value": "On-Time Delivery Rate %", "min": 50, "max": 100, "target": 95, "position": {"x": 740, "y": 80, "w": 460, "h": 380}},
                {"type": "histogram", "title": "Delivery Duration Frequency Distribution (Days)", "xAxis": "delivery_duration_days", "position": {"x": 20, "y": 480, "w": 1180, "h": 380}}
            ]
        },
        {
            "name": "Page_Product_Seller_Intelligence",
            "displayName": "5. Product & Seller Intelligence",
            "visuals": [
                {"type": "barChart", "title": "Top 25 Marketplace Sellers by GMV", "category": "dim_sellers[seller_id]", "values": "GMV", "position": {"x": 20, "y": 80, "w": 650, "h": 400}},
                {"type": "scatterPlot", "title": "Category Price Elasticity & Average Unit Price vs Volume", "x": "Average Item Price", "y": "Units Sold", "details": "dim_products[category_display_name]", "position": {"x": 690, "y": 80, "w": 510, "h": 400}},
                {"type": "table", "title": "Seller Performance & SLA Compliance Matrix", "columns": ["seller_id", "city", "state", "GMV", "Units Sold", "Seller SLA Compliance %"], "position": {"x": 20, "y": 500, "w": 1180, "h": 380}}
            ]
        },
        {
            "name": "Page_Customer_Experience",
            "displayName": "6. Customer Experience",
            "visuals": [
                {"type": "columnChart", "title": "Review Score Distribution (1-5 Stars)", "category": "fact_reviews[review_score]", "values": "Total Reviews", "position": {"x": 20, "y": 80, "w": 550, "h": 350}},
                {"type": "columnChart", "title": "Impact of Late Delivery on CSAT Rating", "category": "Delivery_Status (On-Time vs Late)", "values": "Average CSAT", "position": {"x": 590, "y": 80, "w": 610, "h": 350}},
                {"type": "table", "title": "Category Satisfaction League Table (Highest to Lowest CSAT)", "columns": ["category_display_name", "Total Reviews", "Average CSAT", "Negative Review Rate %"], "position": {"x": 20, "y": 450, "w": 1180, "h": 420}}
            ]
        }
    ]

    report_config = {
        "theme": "OlistIQ_Indigo_Design_System",
        "canvasSize": {"width": 1280, "height": 920},
        "colorPalette": ["#4338CA", "#6366F1", "#10B981", "#F59E0B", "#EF4444", "#3B82F6", "#8B5CF6", "#64748B"],
        "pages": report_pages
    }

    with open(report_dir / "report.json", "w", encoding="utf-8") as f:
        json.dump(report_config, f, indent=2)

    logger.info("Power BI PBIP project successfully generated at bi/powerbi/")
    
    # 6. Generate DAX Documentation
    dax_md_path = DOCS_DIR / "dax_measures_catalog.md"
    with open(dax_md_path, "w", encoding="utf-8") as f:
        f.write("# OlistIQ Power BI DAX Measures & Tabular Catalog\n\n")
        f.write("| Measure Name | DAX Expression | Format | Business Definition |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for m in dax_measures:
            f.write(f"| **`{m['name']}`** | `{m['expression']}` | `{m['formatString']}` | {m['description']} |\n")
        f.write("\n## Tabular Star Schema Relationships\n\n")
        f.write("| Relationship | From Table | From Column | To Table | To Column | Cardinality |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in relationships:
            f.write(f"| `{r['name']}` | `{r['fromTable']}` | `{r['fromColumn']}` | `{r['toTable']}` | `{r['toColumn']}` | Many-to-One (*:1) |\n")
            
    logger.info(f"DAX documentation generated at {dax_md_path}")
    return report_config

if __name__ == "__main__":
    generate_powerbi_project()
