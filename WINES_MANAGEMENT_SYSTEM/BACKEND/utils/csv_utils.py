"""
Wines Management System - CSV Utilities
Handles CSV batch imports with comprehensive validation and CSV streaming exports.
"""

import io
import csv
from flask import Response
from db import get_db, execute_query

def generate_csv_response(headers, rows, filename):
    """Generates an RFC 4180 compliant CSV stream response."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    
    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def import_customers_csv(file_stream):
    """Imports customers from CSV: customer_name,phone,email,address"""
    decoded = file_stream.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_cols = {"customer_name"}
    if not reader.fieldnames or not required_cols.issubset({h.strip().lower() for h in reader.fieldnames}):
        return {
            "success": False,
            "inserted": 0,
            "failed": 0,
            "errors": ["CSV missing mandatory column: 'customer_name'"]
        }

    inserted = 0
    failed = 0
    errors = []

    with get_db() as db:
        sql = "INSERT INTO customer (customer_name, phone, email, address) VALUES (%s, %s, %s, %s)"
        if not db.is_mysql:
            sql = sql.replace("%s", "?")
        cur = db.cursor()

        for idx, row in enumerate(reader, start=2):
            clean = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
            name = clean.get("customer_name")
            if not name:
                failed += 1
                errors.append(f"Row {idx}: Customer name is empty.")
                continue

            phone = clean.get("phone") or None
            email = clean.get("email") or None
            address = clean.get("address") or None

            try:
                cur.execute(sql, (name, phone, email, address))
                inserted += 1
            except Exception as exc:
                failed += 1
                errors.append(f"Row {idx} ('{name}'): {str(exc)}")

        db.commit()

    return {
        "success": True,
        "inserted": inserted,
        "failed": failed,
        "errors": errors
    }


def import_suppliers_csv(file_stream):
    """Imports suppliers: supplier_name,phone,email,address"""
    decoded = file_stream.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_cols = {"supplier_name"}
    if not reader.fieldnames or not required_cols.issubset({h.strip().lower() for h in reader.fieldnames}):
        return {
            "success": False,
            "inserted": 0,
            "failed": 0,
            "errors": ["CSV missing mandatory column: 'supplier_name'"]
        }

    inserted = 0
    failed = 0
    errors = []

    with get_db() as db:
        sql = "INSERT INTO supplier (supplier_name, phone, email, address) VALUES (%s, %s, %s, %s)"
        if not db.is_mysql:
            sql = sql.replace("%s", "?")
        cur = db.cursor()

        for idx, row in enumerate(reader, start=2):
            clean = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
            name = clean.get("supplier_name")
            if not name:
                failed += 1
                errors.append(f"Row {idx}: Supplier name is empty.")
                continue

            phone = clean.get("phone") or None
            email = clean.get("email") or None
            address = clean.get("address") or None

            try:
                cur.execute(sql, (name, phone, email, address))
                inserted += 1
            except Exception as exc:
                failed += 1
                errors.append(f"Row {idx} ('{name}'): {str(exc)}")

        db.commit()

    return {
        "success": True,
        "inserted": inserted,
        "failed": failed,
        "errors": errors
    }


def import_wines_csv(file_stream):
    """Imports wines: wine_name,category,price,quantity,supplier_id,description"""
    decoded = file_stream.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_cols = {"wine_name", "category", "price", "supplier_id"}
    if not reader.fieldnames or not required_cols.issubset({h.strip().lower() for h in reader.fieldnames}):
        return {
            "success": False,
            "inserted": 0,
            "failed": 0,
            "errors": ["CSV missing required columns: 'wine_name', 'category', 'price', 'supplier_id'"]
        }

    inserted = 0
    failed = 0
    errors = []

    with get_db() as db:
        wine_sql = "INSERT INTO wine (wine_name, category, price, quantity, supplier_id, description) VALUES (%s, %s, %s, %s, %s, %s)"
        inv_sql = "INSERT INTO inventory (wine_id, stock_quantity, reorder_level) VALUES (%s, %s, 10)"
        if not db.is_mysql:
            wine_sql = wine_sql.replace("%s", "?")
            inv_sql = inv_sql.replace("%s", "?")
        cur = db.cursor()

        for idx, row in enumerate(reader, start=2):
            clean = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
            name = clean.get("wine_name")
            category = clean.get("category")
            price_raw = clean.get("price")
            supplier_id_raw = clean.get("supplier_id")

            if not name or not category or not price_raw or not supplier_id_raw:
                failed += 1
                errors.append(f"Row {idx}: Missing mandatory wine fields.")
                continue

            try:
                price = float(price_raw)
                quantity = int(clean.get("quantity") or 0)
                supplier_id = int(supplier_id_raw)
                description = clean.get("description") or ""

                cur.execute(wine_sql, (name, category, price, quantity, supplier_id, description))
                new_wine_id = getattr(cur, "lastrowid", None)
                if new_wine_id:
                    try:
                        cur.execute(inv_sql, (new_wine_id, quantity))
                    except:
                        pass
                inserted += 1
            except Exception as exc:
                failed += 1
                errors.append(f"Row {idx} ('{name}'): {str(exc)}")

        db.commit()

    return {
        "success": True,
        "inserted": inserted,
        "failed": failed,
        "errors": errors
    }


def import_inventory_csv(file_stream):
    """
    Imports or updates inventory stock records.
    Format: wine_id,stock_quantity,reorder_level
    """
    decoded = file_stream.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    required_cols = {"wine_id", "stock_quantity"}
    if not reader.fieldnames or not required_cols.issubset({h.strip().lower() for h in reader.fieldnames}):
        return {
            "success": False,
            "inserted": 0,
            "failed": 0,
            "errors": ["CSV missing mandatory columns: 'wine_id', 'stock_quantity'"]
        }

    inserted = 0
    failed = 0
    errors = []

    with get_db() as db:
        cur = db.cursor()
        for idx, row in enumerate(reader, start=2):
            clean = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
            w_id_raw = clean.get("wine_id")
            stock_raw = clean.get("stock_quantity")
            reorder_raw = clean.get("reorder_level") or "10"

            if not w_id_raw or not stock_raw:
                failed += 1
                errors.append(f"Row {idx}: wine_id or stock_quantity missing.")
                continue

            try:
                wine_id = int(w_id_raw)
                stock_qty = int(stock_raw)
                reorder_lvl = int(reorder_raw)

                if stock_qty < 0 or reorder_lvl < 0:
                    raise ValueError("Quantities cannot be negative.")

                # Check if wine exists
                check_sql = "SELECT wine_id FROM wine WHERE wine_id = %s" if db.is_mysql else "SELECT wine_id FROM wine WHERE wine_id = ?"
                cur.execute(check_sql, (wine_id,))
                if not cur.fetchone():
                    raise ValueError(f"Wine ID {wine_id} does not exist.")

                # Update or insert into inventory
                if db.is_mysql:
                    upsert_sql = """
                    INSERT INTO inventory (wine_id, stock_quantity, reorder_level)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE stock_quantity = VALUES(stock_quantity), reorder_level = VALUES(reorder_level)
                    """
                    cur.execute(upsert_sql, (wine_id, stock_qty, reorder_lvl))
                    cur.execute("UPDATE wine SET quantity = %s WHERE wine_id = %s", (stock_qty, wine_id))
                else:
                    cur.execute("INSERT OR REPLACE INTO inventory (wine_id, stock_quantity, reorder_level) VALUES (?, ?, ?)", (wine_id, stock_qty, reorder_lvl))
                    cur.execute("UPDATE wine SET quantity = ? WHERE wine_id = ?", (stock_qty, wine_id))

                inserted += 1
            except Exception as exc:
                failed += 1
                errors.append(f"Row {idx} (Wine ID {w_id_raw}): {str(exc)}")

        db.commit()

    return {
        "success": True,
        "inserted": inserted,
        "failed": failed,
        "errors": errors
    }
