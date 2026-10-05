"""
Wines Management System - Dashboard & Analytics API Router
Supplies real-time aggregated metrics, charts data, and analytical reports directly from MySQL.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from database import get_db
import crud
import schemas
import models
from utils.csv_export import generate_csv_stream

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard & Analytics"])


@router.get("/statistics", response_model=schemas.DashboardStatsOut)
def get_statistics(db: Session = Depends(get_db)):
    """Fetch live KPI counts and totals from the database."""
    return crud.get_dashboard_statistics(db)


@router.get("/charts/category")
def get_category_chart(db: Session = Depends(get_db)):
    """Category distribution for Chart.js doughnut chart."""
    return crud.get_category_distribution(db)


@router.get("/charts/monthly-sales")
def get_monthly_sales_chart(db: Session = Depends(get_db)):
    """Monthly sales progression for Chart.js bar/line chart."""
    return crud.get_monthly_sales(db)


@router.get("/charts/stock")
def get_stock_chart(limit: int = Query(12, ge=5, le=50), db: Session = Depends(get_db)):
    """Stock levels compared to reorder levels for Chart.js bar chart."""
    return crud.get_stock_chart_data(db, limit=limit)


# -------------------------------------------------------------
# DETAILED REPORTS SUB-ENDPOINTS
# -------------------------------------------------------------
reports_router = APIRouter(prefix="/api/reports", tags=["Reports"])


@reports_router.get("/sales-by-category")
def report_sales_by_category(db: Session = Depends(get_db)):
    """Aggregates revenue and bottles sold by wine category."""
    results = db.query(
        models.Wine.category,
        func.count(func.distinct(models.Order.order_id)).label("orders_count"),
        func.sum(models.OrderDetail.quantity).label("bottles_sold"),
        func.sum(models.OrderDetail.quantity * models.OrderDetail.unit_price).label("category_revenue"),
        func.round(func.avg(models.OrderDetail.unit_price), 2).label("avg_selling_price")
    ).join(models.OrderDetail, models.Wine.wine_id == models.OrderDetail.wine_id)\
     .join(models.Order, models.OrderDetail.order_id == models.Order.order_id)\
     .group_by(models.Wine.category)\
     .order_by(desc("category_revenue")).all()

    return [{
        "category": r.category,
        "orders_count": r.orders_count or 0,
        "bottles_sold": int(r.bottles_sold or 0),
        "total_revenue": float(r.category_revenue or 0.0),
        "avg_selling_price": float(r.avg_selling_price or 0.0)
    } for r in results]


@reports_router.get("/sales-by-wine")
def report_sales_by_wine(db: Session = Depends(get_db)):
    """Aggregates best-selling wines with bottle volume and revenue."""
    results = db.query(
        models.Wine.wine_id,
        models.Wine.wine_name,
        models.Wine.category,
        func.sum(models.OrderDetail.quantity).label("units_sold"),
        func.sum(models.OrderDetail.quantity * models.OrderDetail.unit_price).label("wine_revenue")
    ).join(models.OrderDetail, models.Wine.wine_id == models.OrderDetail.wine_id)\
     .group_by(models.Wine.wine_id, models.Wine.wine_name, models.Wine.category)\
     .order_by(desc("wine_revenue")).all()

    return [{
        "wine_id": r.wine_id,
        "wine_name": r.wine_name,
        "category": r.category,
        "units_sold": int(r.units_sold or 0),
        "total_revenue": float(r.wine_revenue or 0.0)
    } for r in results]


@reports_router.get("/sales-by-customer")
def report_sales_by_customer(db: Session = Depends(get_db)):
    """Customer spending rankings."""
    results = db.query(
        models.Customer.customer_id,
        models.Customer.customer_name,
        models.Customer.email,
        func.count(models.Order.order_id).label("total_orders"),
        func.sum(models.Order.total_amount).label("total_spent")
    ).join(models.Order, models.Customer.customer_id == models.Order.customer_id)\
     .group_by(models.Customer.customer_id, models.Customer.customer_name, models.Customer.email)\
     .order_by(desc("total_spent")).all()

    return [{
        "customer_id": r.customer_id,
        "customer_name": r.customer_name,
        "email": r.email or "N/A",
        "total_orders": r.total_orders,
        "total_spent": float(r.total_spent or 0.0)
    } for r in results]


@reports_router.get("/low-stock")
def report_low_stock(db: Session = Depends(get_db)):
    """All items in inventory currently below reorder threshold."""
    return crud.get_inventory(db=db, low_stock_only=True, limit=500)


@reports_router.get("/export/csv")
def download_sales_report_csv(report_type: str = Query("category"), db: Session = Depends(get_db)):
    """Exports chosen analytical report as CSV file."""
    if report_type == "customer":
        data = report_sales_by_customer(db)
        headers = ["customer_id", "customer_name", "email", "total_orders", "total_spent"]
        rows = [[d["customer_id"], d["customer_name"], d["email"], d["total_orders"], d["total_spent"]] for d in data]
        return generate_csv_stream(headers, rows, "sales_by_customer.csv")
    elif report_type == "wine":
        data = report_sales_by_wine(db)
        headers = ["wine_id", "wine_name", "category", "units_sold", "total_revenue"]
        rows = [[d["wine_id"], d["wine_name"], d["category"], d["units_sold"], d["total_revenue"]] for d in data]
        return generate_csv_stream(headers, rows, "sales_by_wine.csv")
    else:
        data = report_sales_by_category(db)
        headers = ["category", "orders_count", "bottles_sold", "total_revenue", "avg_selling_price"]
        rows = [[d["category"], d["orders_count"], d["bottles_sold"], d["total_revenue"], d["avg_selling_price"]] for d in data]
        return generate_csv_stream(headers, rows, "sales_by_category.csv")
