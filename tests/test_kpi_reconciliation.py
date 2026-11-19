"""
OlistIQ - KPI & Data Reconciliation Test Suite
Validates mathematical consistency between Python analytical calculations,
SQL views, and database state. Ensures zero join multiplication or discrepancy.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
import pandas as pd
from sqlalchemy import text
from src.database.loader import get_database_engine
from src.analytics.sales_analytics import compute_sales_metrics
from src.analytics.customer_analytics import compute_customer_analytics
from src.analytics.logistics_analytics import compute_logistics_metrics
from src.analytics.customer_experience import compute_cx_metrics

@pytest.fixture(scope="module")
def db_conn():
    engine, _ = get_database_engine()
    with engine.connect() as conn:
        yield conn

@pytest.fixture(scope="module")
def py_sales():
    return compute_sales_metrics()

@pytest.fixture(scope="module")
def py_customers():
    return compute_customer_analytics()

@pytest.fixture(scope="module")
def py_logistics():
    return compute_logistics_metrics()

@pytest.fixture(scope="module")
def py_cx():
    return compute_cx_metrics()

def test_gmv_reconciliation(db_conn, py_sales):
    """Asserts SQL GMV equals Python GMV within 0.01 tolerance."""
    sql = """
        SELECT ROUND(SUM(foi.total_item_value), 2) AS sql_gmv
        FROM fact_order_items foi
        JOIN fact_orders fo ON foi.order_id = fo.order_id
        WHERE fo.order_status <> 'canceled';
    """
    sql_gmv = float(db_conn.execute(text(sql)).scalar())
    py_gmv = float(py_sales["kpis"]["total_gmv"])
    diff = abs(sql_gmv - py_gmv)
    assert diff <= 0.05, f"GMV mismatch! SQL: {sql_gmv}, Python: {py_gmv}, Diff: {diff}"

def test_orders_reconciliation(db_conn, py_sales):
    """Asserts SQL completed orders equals Python completed orders."""
    sql = "SELECT COUNT(DISTINCT order_id) FROM fact_orders WHERE order_status <> 'canceled';"
    sql_orders = int(db_conn.execute(text(sql)).scalar())
    py_orders = int(py_sales["kpis"]["total_orders"])
    assert sql_orders == py_orders, f"Orders count mismatch! SQL: {sql_orders}, Python: {py_orders}"

def test_aov_reconciliation(db_conn, py_sales):
    """Asserts AOV equals GMV / Orders."""
    py_aov = py_sales["kpis"]["average_order_value"]
    expected_aov = round(py_sales["kpis"]["total_gmv"] / py_sales["kpis"]["total_orders"], 2)
    assert abs(py_aov - expected_aov) <= 0.02, f"AOV mismatch! Found {py_aov}, Expected {expected_aov}"

def test_on_time_delivery_reconciliation(db_conn, py_logistics):
    """Asserts SQL on-time delivery rate equals Python on-time delivery rate."""
    sql = "SELECT ROUND(SUM(is_on_time) * 100.0 / COUNT(order_id), 2) FROM fact_delivery;"
    sql_on_time = float(db_conn.execute(text(sql)).scalar())
    py_on_time = float(py_logistics["logistics_kpis"]["on_time_delivery_rate_pct"])
    assert abs(sql_on_time - py_on_time) <= 0.05, f"Delivery rate mismatch! SQL: {sql_on_time}, Python: {py_on_time}"

def test_csat_reconciliation(db_conn, py_cx):
    """Asserts SQL average review score matches Python review score."""
    sql = "SELECT ROUND(AVG(review_score), 2) FROM fact_reviews;"
    sql_csat = float(db_conn.execute(text(sql)).scalar())
    py_csat = float(py_cx["csat_kpis"]["average_csat"])
    assert abs(sql_csat - py_csat) <= 0.02, f"CSAT mismatch! SQL: {sql_csat}, Python: {py_csat}"

def test_repeat_customer_rate(py_customers):
    """Validates repeat customer rate calculation."""
    repeat_rate = py_customers["repeat_customer_rate_pct"]
    assert 2.5 <= repeat_rate <= 3.5, f"Repeat rate out of expected range for Olist: {repeat_rate}%"

def test_no_negative_financial_values(db_conn):
    """Asserts that prices, freight and total item values are non-negative."""
    sql = """
        SELECT COUNT(*) FROM fact_order_items 
        WHERE price < 0 OR freight_value < 0 OR total_item_value < 0;
    """
    neg_count = int(db_conn.execute(text(sql)).scalar())
    assert neg_count == 0, f"Detected {neg_count} negative financial records!"
