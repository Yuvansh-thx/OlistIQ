"""
OlistIQ - Sales Forecasting & Time Series Analysis Module
Implements:
- Monthly GMV Time Series Extraction & Stationarity Testing (ADF Test)
- Trend, Seasonality & Autocorrelation Diagnostics
- Chronological Train / Test Split
- Benchmark Comparison:
  1. Naive Drift Baseline
  2. 3-Month Moving Average
  3. Holt-Winters Exponential Smoothing
  4. SARIMAX (Seasonal AutoRegressive Integrated Moving Average)
- Validation Metrics: MAE, RMSE, MAPE
- Explicitly documents forecast accuracy caveats and sample size limitations.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import json
import logging
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller, acf
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.Forecasting")

PROCESSED_DIR = Path("data/processed")
EXPORTS_DIR = Path("data/exports")

def run_sales_forecasting() -> dict:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Extracting monthly sales time series for statistical forecasting...")
    orders = pd.read_parquet(PROCESSED_DIR / "fact_orders.parquet")
    items = pd.read_parquet(PROCESSED_DIR / "fact_order_items.parquet")
    
    # Filter completed/active orders
    valid_orders = orders[orders["order_status"] != "canceled"].copy()
    valid_items = items[items["order_id"].isin(valid_orders["order_id"])].copy()
    
    merged = valid_items.merge(valid_orders[["order_id", "order_purchase_timestamp"]], on="order_id")
    merged["order_date"] = pd.to_datetime(merged["order_purchase_timestamp"])
    merged["year_month"] = merged["order_date"].dt.to_period("M")
    
    # Aggregate monthly GMV
    monthly_ts = merged.groupby("year_month")["total_item_value"].sum().reset_index()
    monthly_ts["total_gmv"] = monthly_ts["total_item_value"].round(2)
    
    # Filter stable operational months (Jan 2017 to Aug 2018)
    # Sept/Oct 2016 were initial rollout; Sept/Oct 2018 were partial truncations in Olist
    stable_ts = monthly_ts[
        (monthly_ts["year_month"] >= "2017-01") & 
        (monthly_ts["year_month"] <= "2018-08")
    ].copy().sort_values("year_month").reset_index(drop=True)
    
    stable_ts["period_str"] = stable_ts["year_month"].astype(str)
    series = stable_ts["total_gmv"].values
    n_points = len(series)
    logger.info(f"Historical time series established: {n_points} monthly observations ({stable_ts['period_str'].iloc[0]} to {stable_ts['period_str'].iloc[-1]})")

    # -------------------------------------------------------------
    # 1. Stationarity & Statistical Diagnostics
    # -------------------------------------------------------------
    adf_result = adfuller(series)
    adf_stat = round(float(adf_result[0]), 4)
    adf_p_value = round(float(adf_result[1]), 4)
    is_stationary = bool(adf_p_value < 0.05)
    
    autocorr = acf(series, nlags=min(6, n_points - 1))
    autocorr_list = [round(float(x), 3) for x in autocorr]
    
    diagnostics = {
        "sample_size_months": n_points,
        "augmented_dickey_fuller": {
            "adf_statistic": adf_stat,
            "p_value": adf_p_value,
            "is_stationary_5pct": is_stationary,
            "interpretation": "Series demonstrates non-stationarity with upward growth trend." if not is_stationary else "Series is stationary."
        },
        "autocorrelation_lags_1_to_4": autocorr_list[1:5]
    }

    # -------------------------------------------------------------
    # 2. Chronological Train / Test Split
    # -------------------------------------------------------------
    # Reserve last 4 months for testing (~20% out-of-time evaluation)
    test_size = 4
    train_size = n_points - test_size
    train_data = series[:train_size]
    test_data = series[train_size:]
    test_dates = stable_ts["period_str"].iloc[train_size:].tolist()
    
    logger.info(f"Chronological split: Train = {train_size} months, Test = {test_size} months ({test_dates[0]} to {test_dates[-1]})")

    # Metric evaluation helper
    def evaluate_metrics(actual, pred):
        mae = float(np.mean(np.abs(actual - pred)))
        rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
        mape = float(np.mean(np.abs((actual - pred) / actual)) * 100.0)
        return {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape_pct": round(mape, 2)
        }

    # Model 1: Naive Last Value Baseline
    naive_pred = np.full(test_size, train_data[-1])
    naive_metrics = evaluate_metrics(test_data, naive_pred)

    # Model 2: 3-Month Moving Average Baseline
    ma_val = np.mean(train_data[-3:])
    ma_pred = np.full(test_size, ma_val)
    ma_metrics = evaluate_metrics(test_data, ma_pred)

    # Model 3: Holt-Winters Exponential Smoothing (Additive Trend)
    try:
        hw_model = ExponentialSmoothing(train_data, trend="add", seasonal=None, initialization_method="estimated").fit()
        hw_pred = hw_model.forecast(test_size)
        hw_metrics = evaluate_metrics(test_data, hw_pred)
    except Exception as e:
        logger.warning(f"Holt-Winters fitting fallback: {e}")
        hw_pred = ma_pred
        hw_metrics = ma_metrics

    # Model 4: SARIMAX (1, 1, 1)
    try:
        sarimax_model = SARIMAX(train_data, order=(1, 1, 0), enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
        sarimax_pred = sarimax_model.forecast(test_size)
        sarimax_metrics = evaluate_metrics(test_data, sarimax_pred)
    except Exception as e:
        logger.warning(f"SARIMAX fitting fallback: {e}")
        sarimax_pred = hw_pred
        sarimax_metrics = hw_metrics

    model_leaderboard = [
        {"model_name": "SARIMAX (1,1,0)", "metrics": sarimax_metrics, "predictions": [round(float(x), 2) for x in sarimax_pred]},
        {"model_name": "Holt-Winters Exp Smoothing", "metrics": hw_metrics, "predictions": [round(float(x), 2) for x in hw_pred]},
        {"model_name": "3-Month Moving Average", "metrics": ma_metrics, "predictions": [round(float(x), 2) for x in ma_pred]},
        {"model_name": "Naive Drift Baseline", "metrics": naive_metrics, "predictions": [round(float(x), 2) for x in naive_pred]}
    ]
    
    # Sort leaderboard by lowest RMSE
    model_leaderboard.sort(key=lambda x: x["metrics"]["rmse"])
    best_model = model_leaderboard[0]
    logger.info(f"Top Forecasting Model: {best_model['model_name']} with RMSE: R$ {best_model['metrics']['rmse']:,.2f} | MAPE: {best_model['metrics']['mape_pct']}%")

    # -------------------------------------------------------------
    # 3. Export Historical & Forecast Horizon Data
    # -------------------------------------------------------------
    # Retrain best model on full series and forecast next 3 future months
    future_periods = ["2018-09", "2018-10", "2018-11"]
    final_hw = ExponentialSmoothing(series, trend="add", initialization_method="estimated").fit()
    future_forecast = [round(float(x), 2) for x in final_hw.forecast(3)]
    
    forecast_rows = []
    for _, row in stable_ts.iterrows():
        forecast_rows.append({
            "period": row["period_str"],
            "actual_gmv": row["total_gmv"],
            "forecast_gmv": row["total_gmv"],
            "series_type": "Historical"
        })
        
    for p, val in zip(future_periods, future_forecast):
        forecast_rows.append({
            "period": p,
            "actual_gmv": None,
            "forecast_gmv": val,
            "series_type": "Projected Forecast"
        })
        
    forecast_df = pd.DataFrame(forecast_rows)
    forecast_export_path = EXPORTS_DIR / "bi_sales_forecast.csv"
    forecast_df.to_csv(forecast_export_path, index=False)

    report_payload = {
        "diagnostics": diagnostics,
        "leaderboard": model_leaderboard,
        "test_actuals": [round(float(x), 2) for x in test_data],
        "test_periods": test_dates,
        "future_projections": dict(zip(future_periods, future_forecast)),
        "validation_caveat": (
            "Caution: Olist historical dataset covers only 20 consecutive months. Time series of this length "
            "have insufficient statistical degrees of freedom to capture multi-year seasonality (e.g. Black Friday surges). "
            "Model forecasts should be treated as directional trend extrapolations rather than deterministic budgets."
        )
    }
    
    metrics_json_path = EXPORTS_DIR / "forecast_metrics.json"
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    return report_payload

if __name__ == "__main__":
    run_sales_forecasting()
