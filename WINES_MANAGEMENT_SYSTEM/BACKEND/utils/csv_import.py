"""
Wines Management System - CSV Import Utility
Validates CSV headers, data types, business constraints, and inserts records into MySQL.
Returns detailed audit reports containing inserted count, failed count, and row-by-row error logs.
"""

import io
import csv
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import models
import crud
import schemas


def import_customers_csv(db: Session, file_content: bytes) -> Dict[str, Any]:
    """Imports customers from CSV with format: customer_name,phone,email,address"""
    decoded = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_headers = {"customer_name"}
    if not reader.fieldnames or not required_headers.issubset({h.strip().lower() for h in reader.fieldnames}):
        return {
            "success": False,
            "inserted": 0,
            "failed": 0,
            "errors": ["CSV missing mandatory column: 'customer_name'"]
        }

    inserted = 0
    failed = 0
    errors: List[str] = []

    for row_idx, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
        name = row.get("customer_name")
        if not name:
            failed += 1
            errors.append(f"Row {row_idx}: 'customer_name' is missing or blank.")
            continue

        try:
            customer_data = schemas.CustomerCreate(
                customer_name=name,
                phone=row.get("phone", None),
                email=row.get("email", None),
                address=row.get("address", None)
            )
            crud.create_customer(db, customer_data)
            inserted += 1
        except Exception as exc:
            failed += 1
            errors.append(f"Row {row_idx} ('{name}'): {str(exc)}")

    return {
        "success": True,
        "inserted": inserted,
        "failed": failed,
        "errors": errors
    }


def import_suppliers_csv(db: Session, file_content: bytes) -> Dict[str, Any]:
    """Imports suppliers from CSV: supplier_name,phone,email,address"""
    decoded = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_headers = {"supplier_name"}
    if not reader.fieldnames or not required_headers.issubset({h.strip().lower() for h in reader.fieldnames}):
        return {
            "success": False,
            "inserted": 0,
            "failed": 0,
            "errors": ["CSV missing mandatory column: 'supplier_name'"]
        }

    inserted = 0
    failed = 0
    errors: List[str] = []

    for row_idx, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
        name = row.get("supplier_name")
        if not name:
            failed += 1
            errors.append(f"Row {row_idx}: 'supplier_name' is missing or blank.")
            continue

        try:
            supplier_data = schemas.SupplierCreate(
                supplier_name=name,
                phone=row.get("phone", None),
                email=row.get("email", None),
                address=row.get("address", None)
            )
            crud.create_supplier(db, supplier_data)
            inserted += 1
        except Exception as exc:
            failed += 1
            errors.append(f"Row {row_idx} ('{name}'): {str(exc)}")

    return {
        "success": True,
        "inserted": inserted,
        "failed": failed,
        "errors": errors
    }


def import_wines_csv(db: Session, file_content: bytes) -> Dict[str, Any]:
    """Imports wines from CSV: wine_name,category,price,quantity,supplier_id"""
    decoded = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_headers = {"wine_name", "category", "price"}
    if not reader.fieldnames or not required_headers.issubset({h.strip().lower() for h in reader.fieldnames}):
        return {
            "success": False,
            "inserted": 0,
            "failed": 0,
            "errors": ["CSV must contain columns: 'wine_name', 'category', 'price'"]
        }

    inserted = 0
    failed = 0
    errors: List[str] = []

    for row_idx, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
        name = row.get("wine_name")
        category = row.get("category")
        price_raw = row.get("price")

        if not name or not category or not price_raw:
            failed += 1
            errors.append(f"Row {row_idx}: missing wine_name, category, or price.")
            continue

        try:
            price = float(price_raw)
            if price <= 0:
                raise ValueError("Price must be greater than zero.")
            quantity = int(row.get("quantity", "0"))
            supplier_id_raw = row.get("supplier_id")
            supplier_id = int(supplier_id_raw) if supplier_id_raw and supplier_id_raw.isdigit() else None

            wine_data = schemas.WineCreate(
                wine_name=name,
                category=category,
                price=price,
                quantity=quantity,
                supplier_id=supplier_id
            )
            crud.create_wine(db, wine_data)
            inserted += 1
        except Exception as exc:
            failed += 1
            errors.append(f"Row {row_idx} ('{name}'): {str(exc)}")

    return {
        "success": True,
        "inserted": inserted,
        "failed": failed,
        "errors": errors
    }


def import_inventory_csv(db: Session, file_content: bytes) -> Dict[str, Any]:
    """
    Imports or updates inventory stock records.
    Format: wine_id,stock_quantity,reorder_level
    Validates:
    - wine_id exists
    - stock_quantity is non-negative integer
    - reorder_level is non-negative integer
    """
    decoded = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_headers = {"wine_id", "stock_quantity"}
    if not reader.fieldnames or not required_headers.issubset({h.strip().lower() for h in reader.fieldnames}):
        return {
            "success": False,
            "inserted": 0,
            "failed": 0,
            "errors": ["CSV must contain columns: 'wine_id', 'stock_quantity'"]
        }

    inserted = 0
    failed = 0
    errors: List[str] = []

    for row_idx, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
        wine_id_raw = row.get("wine_id")
        stock_raw = row.get("stock_quantity")
        reorder_raw = row.get("reorder_level", "10")

        if not wine_id_raw or not stock_raw:
            failed += 1
            errors.append(f"Row {row_idx}: wine_id or stock_quantity missing.")
            continue

        try:
            wine_id = int(wine_id_raw)
            stock_qty = int(stock_raw)
            reorder_lvl = int(reorder_raw)

            if stock_qty < 0 or reorder_lvl < 0:
                raise ValueError("Quantities cannot be negative.")

            wine = crud.get_wine_by_id(db, wine_id)
            if not wine:
                raise ValueError(f"Wine with ID {wine_id} does not exist.")

            inv_data = schemas.InventoryCreate(
                wine_id=wine_id,
                stock_quantity=stock_qty,
                reorder_level=reorder_lvl
            )
            crud.create_inventory(db, inv_data)
            inserted += 1
        except Exception as exc:
            failed += 1
            errors.append(f"Row {row_idx} (Wine ID {wine_id_raw}): {str(exc)}")

    return {
        "success": True,
        "inserted": inserted,
        "failed": failed,
        "errors": errors
    }
