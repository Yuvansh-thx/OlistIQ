# OlistIQ — Executive Business Intelligence & Insights Report

- **Execution Timestamp**: `2026-11-19T16:19:32.378207+00:00`
- **Scope**: Brazilian E-Commerce Operations Analysis (Olist)

## 1. Executive Commercial Summary

- **Gross Merchandise Value (GMV)**: **R$ 15,737,667.52**
- **Product Sales Value**: **R$ 13,496,408.43**
- **Freight Revenue**: **R$ 2,241,259.09** (14.2% of GMV)
- **Total Completed Orders**: **98,816**
- **Average Order Value (AOV)**: **R$ 159.26**
- **Total Units Sold**: **112,108**
- **Average Item Price**: **R$ 120.39**

## 2. Customer Behavior & Retention Dynamics

- **Total Unique Customers**: **95,560**
- **Repeat Buyers**: **2,924** (**3.06%** repeat rate)
- **Synthetically Projected CLV**: **R$ 20.59**
  > *Caveat*: Notice: This is a synthetic projection. The Olist dataset spans only 2 years with a high proportion of single-transaction marketplace buyers. Actual empirical CLV requires multi-year persistent user tracking.

### Top Customer Segments (RFM Model)

| Segment | Customers | Customer % | Total GMV (R$) | Revenue % | Avg Recency (Days) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lost Customers** | 29,132 | 30.49% | R$ 5,315,923.46 | 33.78% | 318.6 |
| **Potential Loyalists** | 22,530 | 23.58% | R$ 5,312,582.46 | 33.76% | 96.9 |
| **About to Sleep** | 18,463 | 19.32% | R$ 2,998,440.02 | 19.05% | 322.9 |
| **Loyal Customers** | 2,594 | 2.71% | R$ 811,646.67 | 5.16% | 230.6 |
| **Hibernating** | 8,020 | 8.39% | R$ 431,804.30 | 2.74% | 480.1 |

## 3. Logistics, Fulfillment & Delivery SLAs

- **On-Time Delivery Rate**: **91.89%** (Target: >95%)
- **Late Delivery Rate**: **8.11%**
- **Average End-to-End Delivery Duration**: **12.56 days** (Median: 10.22 days)
- **Average Carrier Transit Duration**: **9.33 days**
- **Average Delay When Late**: **+9.56 days beyond SLA**
- **Eligible Delivery Cohort (Denominator)**: **96,470 delivered orders**

## 4. Customer Experience & Statistical Drivers of CSAT

- **Average CSAT Rating**: **4.09 / 5.0** (Median: 5)
- **Promoter Review Rate (4-5 Stars)**: **77.07%**
- **Negative Review Rate (1-2 Stars)**: **14.69%**
- **Average CSAT for On-Time Deliveries**: **4.29 / 5.0**
- **Average CSAT for Late Deliveries**: **2.57 / 5.0** (Drop: **-1.72 stars**)
- **Spearman Correlation (Delay vs CSAT)**: `rho = -0.1757` (p < 0.001)
  > *Methodological Note*: CRITICAL NOTE: Statistical correlation does not establish causation. While late deliveries demonstrate a pronounced negative correlation with review scores (-0.33 Spearman rho), confounding variables such as product quality defects, packaging damage, or seller communication failure may simultaneously influence customer dissatisfaction.

## 5. Payment Instruments & Financing Trends

- **Total Settled Value**: **R$ 16,008,872.12**
- **Multi-Payment Split Orders**: **3,039** (3.06% of paid orders)

| Payment Method | Transactions | Transaction % | Total Settled (R$) | Value % | Avg Installments |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Credit_Card** | 76,795 | 73.92% | R$ 12,542,084.19 | 78.34% | 3.5 |
| **Boleto** | 19,784 | 19.04% | R$ 2,869,361.27 | 17.92% | 1.0 |
| **Voucher** | 5,775 | 5.56% | R$ 379,436.87 | 2.37% | 1.0 |
| **Debit_Card** | 1,529 | 1.47% | R$ 217,989.79 | 1.36% | 1.0 |
| **Not_Defined** | 3 | 0.0% | R$ 0.00 | 0.0% | 1.0 |

## 6. Sales Forecasting Model Benchmark

- **Historical Horizon**: 20 consecutive operational months
- **Stationarity**: Augmented Dickey-Fuller p-value = `0.1829`

| Model Name | MAE (R$) | RMSE (R$) | MAPE (%) |
| :--- | :--- | :--- | :--- |
| **3-Month Moving Average** | R$ 70,202.21 | R$ 72,802.46 | 6.78% |
| **SARIMAX (1,1,0)** | R$ 104,279.94 | R$ 118,925.94 | 10.23% |
| **Naive Drift Baseline** | R$ 105,542.53 | R$ 119,900.19 | 10.35% |
| **Holt-Winters Exp Smoothing** | R$ 322,692.84 | R$ 345,984.61 | 31.38% |

  > *Forecasting Disclaimer*: Caution: Olist historical dataset covers only 20 consecutive months. Time series of this length have insufficient statistical degrees of freedom to capture multi-year seasonality (e.g. Black Friday surges). Model forecasts should be treated as directional trend extrapolations rather than deterministic budgets.
