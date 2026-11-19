# OlistIQ Tableau Dashboard Architecture & Integration Guide

## Overview
The OlistIQ Tableau analytical assets are published as a native, fully configured workbook: `bi/tableau/OlistIQ_Analytics.twb`.

## 6 Governed Dashboards
### OlistIQ — Executive Overview
- **Workbook Sheet**: `1_Executive_Overview`
- **Included Visual Components**: Executive_GMV_Trend, Category_Pareto_Donut
- **Interactive Slicers**: Date (Year-Month), Customer State, Product Category

### OlistIQ — Sales Intelligence
- **Workbook Sheet**: `2_Sales_Intelligence`
- **Included Visual Components**: Executive_GMV_Trend
- **Interactive Slicers**: Date (Year-Month), Customer State, Product Category

### OlistIQ — Customer Intelligence
- **Workbook Sheet**: `3_Customer_Intelligence`
- **Included Visual Components**: Customer_RFM_Distribution
- **Interactive Slicers**: Date (Year-Month), Customer State, Product Category

### OlistIQ — Logistics Intelligence
- **Workbook Sheet**: `4_Logistics_Intelligence`
- **Included Visual Components**: Delivery_SLA_State_Map
- **Interactive Slicers**: Date (Year-Month), Customer State, Product Category

### OlistIQ — Product & Seller Intelligence
- **Workbook Sheet**: `5_Product_Seller_Intelligence`
- **Included Visual Components**: Seller_League_Table, Category_Pareto_Donut
- **Interactive Slicers**: Date (Year-Month), Customer State, Product Category

### OlistIQ — Customer Experience & CSAT
- **Workbook Sheet**: `6_Customer_Experience`
- **Included Visual Components**: CSAT_Distribution_Delay_Impact
- **Interactive Slicers**: Date (Year-Month), Customer State, Product Category

## Tableau Hyper Extract Script
To compile datasets into `.hyper` format when Tableau Hyper API is present, execute:
```bash
python src/database/export_to_hyper.py
```
