"""
Wines Management System - CSV Export Utility
Generates CSV streams directly from database records for real-time downloads.
"""

import io
import csv
from typing import List, Dict, Any
from fastapi.responses import StreamingResponse


def generate_csv_stream(headers: List[str], rows: List[List[Any]], filename: str) -> StreamingResponse:
    """Creates a StreamingResponse formatted as an RFC 4180 CSV file."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    output.seek(0)
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def export_customers_csv(customers: List[Dict[str, Any]]) -> StreamingResponse:
    headers = ["customer_id", "customer_name", "phone", "email", "address", "total_orders", "total_spent"]
    rows = []
    for c in customers:
        rows.append([
            c.get("customer_id"),
            c.get("customer_name"),
            c.get("phone", ""),
            c.get("email", ""),
            c.get("address", ""),
            c.get("total_orders", 0),
            c.get("total_spent", 0.0)
        ])
    return generate_csv_stream(headers, rows, "customers_export.csv")


def export_suppliers_csv(suppliers: List[Dict[str, Any]]) -> StreamingResponse:
    headers = ["supplier_id", "supplier_name", "phone", "email", "address", "wine_count"]
    rows = []
    for s in suppliers:
        rows.append([
            s.get("supplier_id"),
            s.get("supplier_name"),
            s.get("phone", ""),
            s.get("email", ""),
            s.get("address", ""),
            s.get("wine_count", 0)
        ])
    return generate_csv_stream(headers, rows, "suppliers_export.csv")


def export_wines_csv(wines: List[Dict[str, Any]]) -> StreamingResponse:
    headers = ["wine_id", "wine_name", "category", "price", "quantity", "supplier_id", "supplier_name"]
    rows = []
    for w in wines:
        rows.append([
            w.get("wine_id"),
            w.get("wine_name"),
            w.get("category"),
            w.get("price"),
            w.get("quantity"),
            w.get("supplier_id", ""),
            w.get("supplier_name", "")
        ])
    return generate_csv_stream(headers, rows, "wines_export.csv")


def export_inventory_csv(items: List[Dict[str, Any]]) -> StreamingResponse:
    headers = ["inventory_id", "wine_id", "wine_name", "category", "stock_quantity", "reorder_level", "status", "last_updated"]
    rows = []
    for i in items:
        rows.append([
            i.get("inventory_id"),
            i.get("wine_id"),
            i.get("wine_name"),
            i.get("category"),
            i.get("stock_quantity"),
            i.get("reorder_level"),
            i.get("status"),
            str(i.get("last_updated", ""))
        ])
    return generate_csv_stream(headers, rows, "inventory_export.csv")


def export_orders_csv(orders: List[Dict[str, Any]]) -> StreamingResponse:
    headers = ["order_id", "customer_id", "customer_name", "order_date", "total_amount", "payment_status", "items_count"]
    rows = []
    for o in orders:
        rows.append([
            o.get("order_id"),
            o.get("customer_id"),
            o.get("customer_name"),
            str(o.get("order_date", "")),
            o.get("total_amount"),
            o.get("payment_status"),
            o.get("items_count", 0)
        ])
    return generate_csv_stream(headers, rows, "orders_export.csv")
