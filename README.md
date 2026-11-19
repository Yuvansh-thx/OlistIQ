# OlistIQ — E-Commerce Intelligence & Business Analytics Platform

An end-to-end business intelligence platform analyzing Brazilian e-commerce operations using the Olist dataset.

## Architecture & Technology Stack
- **Ingestion**: KaggleHub (automated data acquisition)
- **Language**: Python 3.12+ (tested on Python 3.14)
- **Processing**: Pandas, NumPy
- **Statistics**: SciPy, Statsmodels
- **Database**: Supabase PostgreSQL (Star Schema, optimized for 500 MB free tier)
- **Database Access**: SQLAlchemy, psycopg
- **Analytics**: Advanced SQL & Python
- **Business Intelligence**:
  - **Power BI**: PBIP project format, DAX measures
  - **Tableau**: Tableau Hyper API, TWB workbooks
  - **Google Looker Studio**: Direct cloud database views
- **Version Control**: Git & GitHub

## Repository Structure
```
OSlit/
├── data/
│   ├── raw/                 # Downloaded raw CSV datasets
│   └── processed/           # Cleaned & transformed parquet files
├── src/
│   ├── ingestion/           # KaggleHub automated acquisition pipeline
│   ├── processing/          # Cleaning, transformation & star schema generation
│   ├── database/            # Supabase PostgreSQL connectivity & loading
│   └── analytics/           # Python statistical analytics & RFM models
├── sql/
│   ├── schema/              # Table schemas & constraints
│   ├── views/               # Aggregated views for BI reporting
│   └── analytics/           # Advanced analytical queries
├── bi/
│   ├── powerbi/             # Power BI Project (PBIP) & DAX code
│   ├── tableau/             # Hyper extraction scripts & TWB models
│   └── looker/              # Looker Studio connection configurations
├── notebooks/               # Jupyter analysis notebooks
├── references/              # UI/UX dashboard benchmark references
├── requirements.txt         # Project dependencies
└── .env.example             # Environment variable template
```

## Setup & Getting Started
1. Clone the repository and navigate into the project:
   ```bash
   git clone <repo-url>
   cd OSlit
   ```
2. Set up virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Configure `.env` with your Supabase credentials:
   ```bash
   cp .env.example .env
   ```
