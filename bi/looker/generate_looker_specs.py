"""
OlistIQ - Google Looker Studio Specification & Linking Engine
Generates governed JSON configurations and linking parameters for 6 Looker Studio dashboards:
1. Executive Overview
2. Sales Intelligence
3. Customer Intelligence
4. Logistics Intelligence
5. Product & Seller Intelligence
6. Customer Experience
Provides exact dimension/metric bindings, calculated field SQL formulas, and theme tokens.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.LookerStudio")

LOOKER_DIR = Path("bi/looker")
DOCS_DIR = Path("docs")

def generate_looker_specifications():
    LOOKER_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Generating Google Looker Studio specification configurations...")
    
    dashboards = [
        {
            "id": "looker_page_1",
            "title": "1. Executive Overview Dashboard",
            "dataSource": "Supabase View: bi_executive_overview / bi_monthly_sales",
            "dateControl": {
                "field": "order_purchase_timestamp",
                "defaultRange": "2017-01-01 to 2018-08-31"
            },
            "filters": [
                {"name": "Customer State", "dimension": "state", "controlType": "Drop-down list"},
                {"name": "Category", "dimension": "category_display_name", "controlType": "Search box"}
            ],
            "scorecards": [
                {"title": "Gross Merchandise Value", "metric": "SUM(total_gmv)", "format": "Currency (BRL)", "sparkline": "month_date"},
                {"title": "Total Orders", "metric": "SUM(total_orders)", "format": "Number", "sparkline": "month_date"},
                {"title": "Average Order Value", "metric": "SUM(total_gmv)/SUM(total_orders)", "format": "Currency (BRL)"},
                {"title": "On-Time Delivery Rate", "metric": "SUM(on_time_deliveries)/SUM(total_delivered_orders)", "format": "Percent"}
            ],
            "charts": [
                {
                    "type": "Time Series Line & Area Chart",
                    "title": "Monthly GMV & Order Velocity Trend",
                    "dimension": "year_month",
                    "metrics": ["SUM(total_gmv)", "SUM(total_orders)"]
                },
                {
                    "type": "Donut Chart",
                    "title": "Top Categories Revenue Distribution",
                    "dimension": "category",
                    "metric": "SUM(category_gmv)",
                    "sliceCount": 8
                },
                {
                    "type": "Geo Map",
                    "title": "Brazilian Regional Sales Concentration",
                    "dimension": "customer_state",
                    "metric": "SUM(total_delivered_orders)",
                    "zoomRegion": "BR"
                }
            ]
        },
        {
            "id": "looker_page_2",
            "title": "2. Sales Intelligence Dashboard",
            "dataSource": "Supabase View: bi_monthly_sales",
            "scorecards": [
                {"title": "Product Sales (Net)", "metric": "SUM(total_product_sales)", "format": "Currency (BRL)"},
                {"title": "Freight Revenue", "metric": "SUM(total_freight_revenue)", "format": "Currency (BRL)"},
                {"title": "Units Sold", "metric": "SUM(total_units_sold)", "format": "Number"}
            ],
            "charts": [
                {
                    "type": "Stacked Bar Chart",
                    "title": "Product Sales vs Freight Revenue by Month",
                    "dimension": "year_month",
                    "metrics": ["SUM(total_product_sales)", "SUM(total_freight_revenue)"]
                },
                {
                    "type": "Table with Heatmap",
                    "title": "Monthly Performance Breakdown",
                    "dimension": "year_month",
                    "metrics": ["total_orders", "total_gmv", "average_order_value", "mom_gmv_growth_pct"]
                }
            ]
        },
        {
            "id": "looker_page_3",
            "title": "3. Customer Intelligence Dashboard",
            "dataSource": "Extract: bi_customer_segments.csv / bi_customer_cohorts.csv",
            "scorecards": [
                {"title": "Total Unique Buyers", "metric": "COUNT_DISTINCT(customer_unique_id)", "format": "Number"},
                {"title": "Repeat Buyer Rate", "metric": "3.06%", "format": "Percent"},
                {"title": "Projected CLV", "metric": "R$ 48.74", "format": "Currency (BRL)"}
            ],
            "charts": [
                {
                    "type": "Bar Chart",
                    "title": "Customer Count by RFM Segment",
                    "dimension": "rfm_segment",
                    "metric": "COUNT(customer_unique_id)",
                    "sort": "DESC"
                },
                {
                    "type": "Pivot Table",
                    "title": "Cohort Retention Matrix (% of Initial Month)",
                    "rowDimension": "cohort_month",
                    "columnDimension": "cohort_index",
                    "metric": "AVG(retention_rate)"
                }
            ]
        },
        {
            "id": "looker_page_4",
            "title": "4. Logistics & SLA Intelligence Dashboard",
            "dataSource": "Supabase View: bi_delivery_performance",
            "scorecards": [
                {"title": "On-Time Delivery Rate", "metric": "91.89%", "format": "Percent"},
                {"title": "Average Delivery Duration", "metric": "12.56 Days", "format": "Number"},
                {"title": "Average Days Ahead of SLA", "metric": "13.01 Days", "format": "Number"}
            ],
            "charts": [
                {
                    "type": "Horizontal Bar Chart",
                    "title": "Average Delivery Days by Customer State",
                    "dimension": "customer_state",
                    "metric": "AVG(avg_delivery_duration_days)",
                    "sort": "ASC"
                },
                {
                    "type": "Scatter Plot",
                    "title": "Delivery Duration vs Late Breach Rate by Region",
                    "xMetric": "avg_delivery_duration_days",
                    "yMetric": "100 - on_time_delivery_rate_pct",
                    "dimension": "customer_state"
                }
            ]
        },
        {
            "id": "looker_page_5",
            "title": "5. Product & Seller Intelligence Dashboard",
            "dataSource": "Supabase View: bi_category_performance / bi_seller_performance",
            "scorecards": [
                {"title": "Active Product Categories", "metric": "72", "format": "Number"},
                {"title": "Active Marketplace Sellers", "metric": "3,095", "format": "Number"},
                {"title": "Average Selling Price", "metric": "R$ 120.65", "format": "Currency (BRL)"}
            ],
            "charts": [
                {
                    "type": "Bar Chart",
                    "title": "Top 15 Categories by GMV Contribution",
                    "dimension": "category",
                    "metric": "SUM(category_gmv)",
                    "sort": "DESC"
                },
                {
                    "type": "Table with Bars",
                    "title": "Top Marketplace Sellers Leaderboard",
                    "dimension": "seller_id",
                    "metrics": ["total_seller_gmv", "total_orders", "avg_seller_review_score", "seller_state"]
                }
            ]
        },
        {
            "id": "looker_page_6",
            "title": "6. Customer Experience & CSAT Dashboard",
            "dataSource": "Supabase View: bi_customer_reviews",
            "scorecards": [
                {"title": "Average Review CSAT", "metric": "4.09 / 5.0", "format": "Rating"},
                {"title": "Promoter Share (4-5 Stars)", "metric": "76.8%", "format": "Percent"},
                {"title": "Detractor Share (1-2 Stars)", "metric": "14.7%", "format": "Percent"}
            ],
            "charts": [
                {
                    "type": "Column Chart",
                    "title": "Rating Score Distribution (1 to 5 Stars)",
                    "dimension": "review_score",
                    "metric": "SUM(total_reviews)"
                },
                {
                    "type": "Bar Chart",
                    "title": "CSAT Drop for On-Time vs Late Deliveries",
                    "dimension": "Delivery Status",
                    "metric": "Average CSAT",
                    "values": [{"On-Time": 4.22}, {"Late": 2.50}]
                }
            ]
        }
    ]

    spec_path = LOOKER_DIR / "looker_studio_specs.json"
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump({"theme": "Indigo_Modern", "dashboards": dashboards}, f, indent=2)
    logger.info(f"Looker Studio JSON configuration saved to {spec_path}")

    # Write Step-by-Step Guide
    guide_path = DOCS_DIR / "looker_studio_guide.md"
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write("# OlistIQ Google Looker Studio Deployment & Configuration Guide\n\n")
        f.write("This guide provides the exact steps to connect Looker Studio to Supabase PostgreSQL or standardized CSV extracts and reproduce the 6 portfolio dashboards.\n\n")
        f.write("## 1. Connecting Data Sources\n\n")
        f.write("### Option A: Direct Supabase PostgreSQL Connection (Live Database)\n")
        f.write("1. Open [Google Looker Studio](https://lookerstudio.google.com/) and click **Create** > **Data Source**.\n")
        f.write("2. Select the **PostgreSQL** connector.\n")
        f.write("3. Enter your Supabase connection parameters:\n")
        f.write("   - **Host**: `aws-0-[region].pooler.supabase.com` (from `.env`)\n")
        f.write("   - **Port**: `6543` (Transaction pooler) or `5432`\n")
        f.write("   - **Database**: `postgres`\n")
        f.write("   - **Username**: `postgres.[your-project-ref]`\n")
        f.write("   - **Password**: `[your-supabase-db-password]`\n")
        f.write("   - Check **Enable SSL**.\n")
        f.write("4. Under **Table**, select the pre-aggregated analytical view: `bi_monthly_sales` (or `bi_executive_overview`).\n\n")
        f.write("### Option B: Standardized CSV Upload (Zero Configuration)\n")
        f.write("1. Upload the pre-generated exports located in `data/exports/`:\n")
        f.write("   - `bi_monthly_sales.csv`\n")
        f.write("   - `bi_category_performance.csv`\n")
        f.write("   - `bi_delivery_performance.csv`\n")
        f.write("   - `bi_customer_segments.csv`\n")
        f.write("   - `bi_customer_reviews.csv`\n\n")
        f.write("## 2. Dashboard Creation Specifications\n\n")
        for db in dashboards:
            f.write(f"### {db['title']}\n")
            f.write(f"- **Data Source Binding**: `{db['dataSource']}`\n")
            f.write("- **Scorecard KPIs**:\n")
            for sc in db["scorecards"]:
                f.write(f"  - **{sc['title']}**: `{sc['metric']}` ({sc['format']})\n")
            f.write("- **Visual Components**:\n")
            for c in db["charts"]:
                f.write(f"  - **{c['title']}** (`{c['type']}`): Dimension = `{c.get('dimension', 'N/A')}`, Metric = `{c.get('metric', c.get('metrics', 'N/A'))}`\n")
            f.write("\n")

    logger.info(f"Looker Studio deployment guide generated at {guide_path}")
    return spec_path

if __name__ == "__main__":
    generate_looker_specifications()
