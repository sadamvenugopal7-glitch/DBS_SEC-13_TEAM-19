"""
Wines Management System - Inventory Routes
Handles Inventory listing with dynamic status computation (IN STOCK, LOW STOCK, OUT OF STOCK),
transaction-based stock addition and stock removal, stock level updates,
CSV import and CSV export.
"""

from flask import Blueprint, request, jsonify
from db import get_db, execute_query
from utils.csv_utils import generate_csv_response, import_inventory_csv

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

@inventory_bp.route("", methods=["GET"])
def list_inventory():
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip().upper()
    sort_by = request.args.get("sort_by", "inventory_id")
    sort_order = request.args.get("sort_order", "asc").upper()

    valid_sort_cols = {"inventory_id", "wine_name", "category", "stock_quantity", "reorder_level", "price", "supplier_name", "last_updated"}
    if sort_by not in valid_sort_cols:
        sort_by = "inventory_id"
    if sort_order not in ("ASC", "DESC"):
        sort_order = "ASC"

    col_mapping = {
        "inventory_id": "i.inventory_id",
        "wine_name": "w.wine_name",
        "category": "w.category",
        "stock_quantity": "i.stock_quantity",
        "reorder_level": "i.reorder_level",
        "price": "w.price",
        "supplier_name": "s.supplier_name",
        "last_updated": "i.last_updated"
    }

    sql = """
        SELECT 
            i.inventory_id,
            i.wine_id,
            w.wine_name,
            w.category,
            w.price,
            s.supplier_name,
            i.stock_quantity,
            i.reorder_level,
            i.last_updated,
            CASE 
                WHEN i.stock_quantity = 0 THEN 'OUT OF STOCK'
                WHEN i.stock_quantity <= i.reorder_level THEN 'LOW STOCK'
                ELSE 'IN STOCK'
            END AS status
        FROM inventory i
        JOIN wine w ON i.wine_id = w.wine_id
        JOIN supplier s ON w.supplier_id = s.supplier_id
        WHERE 1=1
    """
    params = []

    if search:
        sql += " AND (w.wine_name LIKE %s OR w.category LIKE %s OR s.supplier_name LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if status_filter in ("IN STOCK", "LOW STOCK", "OUT OF STOCK"):
        if status_filter == "OUT OF STOCK":
            sql += " AND i.stock_quantity = 0"
        elif status_filter == "LOW STOCK":
            sql += " AND i.stock_quantity > 0 AND i.stock_quantity <= i.reorder_level"
        elif status_filter == "IN STOCK":
            sql += " AND i.stock_quantity > i.reorder_level"

    sql += f" ORDER BY {col_mapping[sort_by]} {sort_order}"

    items = execute_query(sql, params)
    return jsonify(items)


@inventory_bp.route("/add", methods=["POST"])
def add_stock():
    """
    Adds quantity to wine stock using an ACID transaction.
    Updates both wine.quantity and inventory.stock_quantity.
    """
    data = request.get_json() or {}
    wine_id = data.get("wine_id")
    quantity_to_add = data.get("quantity")

    if not wine_id:
        return jsonify({"success": False, "message": "Wine selection is required."}), 400

    try:
        quantity_to_add = int(quantity_to_add)
        if quantity_to_add <= 0:
            return jsonify({"success": False, "message": "Quantity to add must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid quantity."}), 400

    with get_db() as db:
        cur = db.cursor()
        # Verify wine exists
        w_sql = "SELECT wine_id, wine_name FROM wine WHERE wine_id = %s" if db.is_mysql else "SELECT wine_id, wine_name FROM wine WHERE wine_id = ?"
        cur.execute(w_sql, (wine_id,))
        wine_row = cur.fetchone()
        if not wine_row:
            return jsonify({"success": False, "message": "Wine not found."}), 404

        # Update inventory
        inv_sql = "UPDATE inventory SET stock_quantity = stock_quantity + %s WHERE wine_id = %s" if db.is_mysql else "UPDATE inventory SET stock_quantity = stock_quantity + ? WHERE wine_id = ?"
        cur.execute(inv_sql, (quantity_to_add, wine_id))

        # Update wine quantity
        wine_upd = "UPDATE wine SET quantity = quantity + %s WHERE wine_id = %s" if db.is_mysql else "UPDATE wine SET quantity = quantity + ? WHERE wine_id = ?"
        cur.execute(wine_upd, (quantity_to_add, wine_id))

        # Read new stock
        sel_sql = "SELECT stock_quantity FROM inventory WHERE wine_id = %s" if db.is_mysql else "SELECT stock_quantity FROM inventory WHERE wine_id = ?"
        cur.execute(sel_sql, (wine_id,))
        new_stock = cur.fetchone()[0]

        db.commit()

    return jsonify({
        "success": True,
        "message": f"Successfully added {quantity_to_add} units to stock.",
        "new_stock": new_stock
    })


@inventory_bp.route("/remove", methods=["POST"])
def remove_stock():
    """
    Removes quantity from wine stock using an ACID transaction.
    Verifies that sufficient stock exists to prevent negative stock.
    """
    data = request.get_json() or {}
    wine_id = data.get("wine_id")
    quantity_to_remove = data.get("quantity")

    if not wine_id:
        return jsonify({"success": False, "message": "Wine selection is required."}), 400

    try:
        quantity_to_remove = int(quantity_to_remove)
        if quantity_to_remove <= 0:
            return jsonify({"success": False, "message": "Quantity to remove must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid quantity."}), 400

    with get_db() as db:
        cur = db.cursor()
        # Verify wine & current inventory
        sel_sql = "SELECT stock_quantity FROM inventory WHERE wine_id = %s" if db.is_mysql else "SELECT stock_quantity FROM inventory WHERE wine_id = ?"
        cur.execute(sel_sql, (wine_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Inventory record not found for this wine."}), 404

        current_stock = row[0]
        if current_stock < quantity_to_remove:
            return jsonify({
                "success": False,
                "message": f"Insufficient stock. Available: {current_stock}, Requested to remove: {quantity_to_remove}."
            }), 400

        # Decrement stock
        inv_sql = "UPDATE inventory SET stock_quantity = stock_quantity - %s WHERE wine_id = %s" if db.is_mysql else "UPDATE inventory SET stock_quantity = stock_quantity - ? WHERE wine_id = ?"
        cur.execute(inv_sql, (quantity_to_remove, wine_id))

        wine_upd = "UPDATE wine SET quantity = quantity - %s WHERE wine_id = %s" if db.is_mysql else "UPDATE wine SET quantity = quantity - ? WHERE wine_id = ?"
        cur.execute(wine_upd, (quantity_to_remove, wine_id))

        new_stock = current_stock - quantity_to_remove
        db.commit()

    return jsonify({
        "success": True,
        "message": f"Successfully removed {quantity_to_remove} units from stock.",
        "new_stock": new_stock
    })


@inventory_bp.route("/<int:inventory_id>", methods=["PUT"])
def update_inventory_record(inventory_id):
    data = request.get_json() or {}
    stock_qty = data.get("stock_quantity")
    reorder_lvl = data.get("reorder_level")

    try:
        stock_qty = int(stock_qty)
        reorder_lvl = int(reorder_lvl)
        if stock_qty < 0 or reorder_lvl < 0:
            return jsonify({"success": False, "message": "Quantities cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid numeric values for stock or reorder level."}), 400

    with get_db() as db:
        cur = db.cursor()
        sel = "SELECT wine_id FROM inventory WHERE inventory_id = %s" if db.is_mysql else "SELECT wine_id FROM inventory WHERE inventory_id = ?"
        cur.execute(sel, (inventory_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Inventory record not found."}), 404

        wine_id = row[0]

        upd_inv = "UPDATE inventory SET stock_quantity = %s, reorder_level = %s WHERE inventory_id = %s" if db.is_mysql else "UPDATE inventory SET stock_quantity = ?, reorder_level = ? WHERE inventory_id = ?"
        cur.execute(upd_inv, (stock_qty, reorder_lvl, inventory_id))

        upd_wine = "UPDATE wine SET quantity = %s WHERE wine_id = %s" if db.is_mysql else "UPDATE wine SET quantity = ? WHERE wine_id = ?"
        cur.execute(upd_wine, (stock_qty, wine_id))

        db.commit()

    return jsonify({"success": True, "message": "Inventory levels updated successfully."})


@inventory_bp.route("/<int:inventory_id>", methods=["DELETE"])
def delete_inventory_record(inventory_id):
    check_sql = "SELECT inventory_id FROM inventory WHERE inventory_id = %s"
    if not execute_query(check_sql, (inventory_id,), fetch_one=True):
        return jsonify({"success": False, "message": "Inventory record not found."}), 404

    sql = "DELETE FROM inventory WHERE inventory_id = %s"
    execute_query(sql, (inventory_id,), commit=True)
    return jsonify({"success": True, "message": "Inventory record deleted successfully."})


@inventory_bp.route("/import", methods=["POST"])
def upload_inventory_csv():
    if "file" not in request.files:
        return jsonify({"success": False, "errors": ["No file uploaded."]}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "errors": ["File must be a .csv."]}), 400
    result = import_inventory_csv(file.stream)
    return jsonify(result)


@inventory_bp.route("/export", methods=["GET"])
@inventory_bp.route("/export/csv", methods=["GET"])
def export_inventory():
    sql = """
        SELECT 
            i.inventory_id,
            i.wine_id,
            w.wine_name,
            w.category,
            i.stock_quantity,
            i.reorder_level,
            w.price,
            s.supplier_name,
            i.last_updated
        FROM inventory i
        JOIN wine w ON i.wine_id = w.wine_id
        JOIN supplier s ON w.supplier_id = s.supplier_id
        ORDER BY i.inventory_id
    """
    items = execute_query(sql)
    headers = ["inventory_id", "wine_id", "wine_name", "category", "stock_quantity", "reorder_level", "price", "supplier_name", "last_updated"]
    rows = [
        [
            it["inventory_id"],
            it["wine_id"],
            it["wine_name"],
            it["category"],
            it["stock_quantity"],
            it["reorder_level"],
            f"{float(it['price']):.2f}",
            it["supplier_name"],
            str(it["last_updated"])
        ]
        for it in items
    ]
    return generate_csv_response(headers, rows, "inventory.csv")
