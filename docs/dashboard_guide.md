# OlistIQ — Dashboard User & Implementation Guide

This guide details the layout, visual structure, slicer interactions, and business analysis for the 6 core dashboard pages across Power BI, Tableau, and Looker Studio.

---

## 1. Executive Overview Dashboard
* **Target Audience**: C-Suite, VP of E-Commerce, Commercial Directors.
* **Core Business Question**: How is the overall marketplace performing in revenue velocity, fulfillment reliability, and customer satisfaction?
* **Components**:
  1. **Hero KPI Cards**: Gross Merchandise Value (R$ 15.74M), Total Completed Orders (98,816), Average Order Value (R$ 159.26), On-Time Delivery Rate (91.89%), Average CSAT (4.09 / 5.0).
  2. **Temporal Velocity**: Monthly GMV line chart with MoM growth percentage indicator.
  3. **Category Concentration**: Donut chart displaying top category contributions.
  4. **Geographic Distribution**: Brazilian state choropleth map highlighting customer demand clusters (São Paulo dominating with >40% of orders).

---

## 2. Sales Intelligence Dashboard
* **Target Audience**: Revenue Operations, Category Managers.
* **Core Business Question**: What is the split between product price and shipping charges, and how is revenue distributed across seasons?
* **Components**:
  1. **Revenue Waterfall**: Product Sales (R$ 13.49M) vs Freight Collection (R$ 2.25M).
  2. **Monthly Performance Matrix**: Tabular view of monthly orders, units sold, GMV, and AOV.

---

## 3. Customer Intelligence Dashboard
* **Target Audience**: Growth Marketing, CRM, Retention Teams.
* **Core Business Question**: Who are our high-value repeat customers, and what are our customer retention retention rates?
* **Components**:
  1. **RFM Segmentation Matrix**: Distribution of customers across Champions, Loyal Customers, Potential Loyalists, and Hibernating buyers.
  2. **Loyalty Share**: Single-order buyers (96.94%) vs Repeat buyers (3.06%).
  3. **Cohort Retention Heatmap**: Monthly acquisition cohort triangles tracing retention decay over time.

---

## 4. Logistics Intelligence Dashboard
* **Target Audience**: Supply Chain, Carrier Operations, Fulfillment Managers.
* **Core Business Question**: Where are our delivery bottlenecks, and how often are shipping promises breached?
* **Components**:
  1. **Regional SLA Performance**: On-time delivery rate by customer state (e.g., SP at 94% vs remote Northern states at 82%).
  2. **Lead Time Analysis**: Distribution of order-to-delivery duration (Average: 12.56 days).
  3. **SLA Breach Penalty**: Quantification of late delivery duration (+9.56 days when delayed).

---

## 5. Product & Seller Intelligence Dashboard
* **Target Audience**: Merchant Partnership Teams, Vendor Managers.
* **Core Business Question**: Who are our top performing merchants, and which categories drive our catalog margins?
* **Components**:
  1. **Seller Revenue League Table**: Top 25 sellers ranked by total GMV, volume, and customer review scores.
  2. **Category Price Elasticity**: Scatter plot comparing average unit price against volume sold.

---

## 6. Customer Experience Dashboard
* **Target Audience**: Customer Experience (CX) Directors, Support Operations.
* **Core Business Question**: What drives customer dissatisfaction, and what is the CSAT penalty for late logistics?
* **Components**:
  1. **CSAT Score Breakdown**: 1 to 5 star rating distribution (76.8% Promoters vs 14.7% Detractors).
  2. **Fulfillment vs Sentiment Correlation**: On-time orders average 4.22 CSAT, while late deliveries plummet to 2.50 CSAT (-1.72 star penalty).
