# OlistIQ — Deployment & Configuration Guide

## 1. Prerequisites
- Python 3.12+ (tested on Python 3.14.6 arm64)
- Git
- Free Supabase Account ([supabase.com](https://supabase.com))
- Free Kaggle Account (optional API key if exceeding unauthenticated rate limits)

## 2. Local Setup
```bash
# 1. Clone repository
git clone <repository_url>
cd OSlit

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## 3. Configuring Supabase PostgreSQL
1. Create a free project on [Supabase](https://supabase.com).
2. Navigate to **Project Settings** > **Database** > **Connection string**.
3. Select **URI** or **Parameters** (use the Transaction Pooler port `6543`).
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Update `.env` with your credentials:
   ```ini
   SUPABASE_DB_HOST=aws-0-us-east-1.pooler.supabase.com
   SUPABASE_DB_PORT=6543
   SUPABASE_DB_NAME=postgres
   SUPABASE_DB_USER=postgres.your-project-ref
   SUPABASE_DB_PASSWORD=your-secure-password
   ```

## 4. Running the Full End-to-End Pipeline
Execute:
```bash
python main.py --stage all
```

Or run modular stages individually:
```bash
# Stage 1: Download & validate raw Kaggle dataset
python main.py --stage ingestion

# Stage 2: Clean, impute, & build dimensional Star Schema
python main.py --stage cleaning

# Stage 3: Run SQL migrations & load Supabase PostgreSQL
python main.py --stage database

# Stage 4: Run advanced SQL & Python statistical analytics
python main.py --stage analytics

# Stage 5: Compile Power BI PBIP, Tableau TWB, & Looker Studio specs
python main.py --stage exports
```

## 5. Running Automated Verification Tests
```bash
pytest tests/ -v
```
All 7 reconciliation and data integrity tests will execute, validating GMV, orders, AOV, on-time delivery, CSAT, and non-negativity constraints.
