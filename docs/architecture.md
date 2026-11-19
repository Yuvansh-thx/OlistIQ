# OlistIQ — System Architecture & Data Engineering Specification

## 1. High-Level Architectural Flow

```mermaid
flowchart TD
    subgraph Data Acquisition
        K[KaggleHub API] -->|Automated Dataset Pull| R[data/raw/ (9 CSVs)]
    end

    subgraph Data Engineering & Quality
        R --> V[Raw Validation & Schema Profiling]
        V --> C[Data Quality & Imputation Engine]
        C -->|97% Compression via Centroids| G[dim_geography]
        C --> T[Star Schema Dimensional Modeling]
    end

    subgraph Central Data Warehouse
        T -->|Batch Multi-Row Insert / COPY| S[(Supabase PostgreSQL)]
        S -->|Views & Materialized Rollups| V1[bi_monthly_sales]
        S --> V2[bi_category_performance]
        S --> V3[bi_delivery_performance]
        S --> V4[bi_payment_analysis]
        S --> V5[bi_customer_reviews]
        S --> V6[bi_executive_overview]
    end

    subgraph Statistical Analytics
        S --> A1[RFM Segmentation & Cohort Matrix]
        S --> A2[Delivery SLA & CSAT Correlation]
        S --> A3[Time Series Forecasting]
    end

    subgraph Multi-Platform BI Triad
        V1 & V2 & V3 & V4 & V5 & V6 --> P[Power BI (PBIP & DAX)]
        V1 & V2 & V3 & V4 & V5 & V6 --> TB[Tableau (Hyper & TWB)]
        V1 & V2 & V3 & V4 & V5 & V6 --> L[Google Looker Studio]
    end
```

## 2. Core Architectural Principles
1. **Modularity**: Strict separation between data ingestion (`src/ingestion`), cleaning and transformation (`src/processing`), database engineering (`src/database`), statistical analytics (`src/analytics`), and BI generation (`bi/`).
2. **Idempotency**: All ingestion, cleaning, and database loading scripts can be rerun safely without introducing duplicate records or data corruption.
3. **Storage Governance**: Optimizes PostgreSQL storage to ensure the database consumes ~130 MB, safely respecting Supabase's 500 MB free-tier quota.
4. **Resilience**: Features automatic local fallback to SQLite for local verification when live Supabase cloud credentials are not supplied.
