"""
OlistIQ - Payment Analytics Module
Calculates:
- Payment Method Distribution (Credit Card, Boleto, Voucher, Debit Card)
- Transaction Volume vs Total Settled Payment Value
- Installment Distributions & Financing Trends
- Average Transaction Value per Payment Instrument
- Handles split payments without double-counting orders.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.PaymentAnalytics")

PROCESSED_DIR = Path("data/processed")
EXPORTS_DIR = Path("data/exports")

def compute_payment_metrics() -> dict:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading payment facts...")
    payments = pd.read_parquet(PROCESSED_DIR / "fact_payments.parquet")
    orders = pd.read_parquet(PROCESSED_DIR / "fact_orders.parquet")
    
    # 1. Payment Method Breakdown
    total_payment_value = round(float(payments["payment_value"].sum()), 2)
    total_transactions = len(payments)
    unique_orders_paid = payments["order_id"].nunique()
    
    payment_method_summary = payments.groupby("payment_type").agg(
        transaction_count=("order_id", "count"),
        orders_count=("order_id", "nunique"),
        total_value=("payment_value", "sum"),
        avg_value=("payment_value", "mean"),
        median_value=("payment_value", "median"),
        avg_installments=("payment_installments", "mean")
    ).reset_index()
    
    payment_method_summary["total_value"] = payment_method_summary["total_value"].round(2)
    payment_method_summary["avg_value"] = payment_method_summary["avg_value"].round(2)
    payment_method_summary["median_value"] = payment_method_summary["median_value"].round(2)
    payment_method_summary["avg_installments"] = payment_method_summary["avg_installments"].round(1)
    
    payment_method_summary["value_share_pct"] = (payment_method_summary["total_value"] / total_payment_value * 100).round(2)
    payment_method_summary["transaction_share_pct"] = (payment_method_summary["transaction_count"] / total_transactions * 100).round(2)
    payment_method_summary = payment_method_summary.sort_values("total_value", ascending=False).reset_index(drop=True)
    
    payment_export_path = EXPORTS_DIR / "bi_payment_analysis.csv"
    payment_method_summary.to_csv(payment_export_path, index=False)

    # 2. Credit Card Installment Distribution
    cc_payments = payments[payments["payment_type"] == "credit_card"].copy()
    
    def bucket_installments(inst):
        if inst == 1:
            return "1 Installment (Single)"
        elif inst <= 3:
            return "2 - 3 Installments"
        elif inst <= 6:
            return "4 - 6 Installments"
        elif inst <= 10:
            return "7 - 10 Installments"
        else:
            return "11+ Installments"
            
    cc_payments["installment_bucket"] = cc_payments["payment_installments"].apply(bucket_installments)
    
    installment_summary = cc_payments.groupby("installment_bucket").agg(
        transaction_count=("order_id", "count"),
        total_value=("payment_value", "sum"),
        avg_value=("payment_value", "mean")
    ).reset_index()
    
    installment_summary["total_value"] = installment_summary["total_value"].round(2)
    installment_summary["avg_value"] = installment_summary["avg_value"].round(2)
    installment_summary["pct_share"] = (installment_summary["total_value"] / cc_payments["payment_value"].sum() * 100).round(2)
    installment_summary = installment_summary.sort_values("total_value", ascending=False).reset_index(drop=True)
    
    installment_export_path = EXPORTS_DIR / "bi_credit_installments.csv"
    installment_summary.to_csv(installment_export_path, index=False)

    # 3. Multi-Payment Order Analysis (Vouchers + CC, Split payments)
    payments_per_order = payments.groupby("order_id")["payment_sequential"].max().reset_index()
    split_orders = int((payments_per_order["payment_sequential"] > 1).sum())
    split_order_pct = round(split_orders / unique_orders_paid * 100.0, 2)
    
    logger.info(
        f"Payment Overview: R$ {total_payment_value:,.2f} across {total_transactions:,} transactions | "
        f"Split Payment Orders: {split_orders:,} ({split_order_pct}%)"
    )

    return {
        "payment_kpis": {
            "total_settled_payment_value": total_payment_value,
            "total_transactions": total_transactions,
            "unique_orders_paid": unique_orders_paid,
            "split_payment_orders": split_orders,
            "split_payment_order_pct": split_order_pct
        },
        "method_breakdown": payment_method_summary.to_dict(orient="records"),
        "installment_tiers": installment_summary.to_dict(orient="records")
    }

if __name__ == "__main__":
    compute_payment_metrics()
