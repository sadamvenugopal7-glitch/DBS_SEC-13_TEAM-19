"""
Wines Management System - Wine Routes
Handles Wine CRUD, search, category filter, price/stock sort,
safe delete check (blocks if order details exist), CSV import, and CSV export.
"""

from flask import Blueprint, request, jsonify
from db import get_db, execute_query
from utils.csv_utils import generate_csv_response, import_wines_csv

wine_bp = Blueprint("wines", __name__, url_prefix="/api/wines")

@wine_bp.route("", methods=["GET"])
def list_wines():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort_by = request.args.get("sort_by", "wine_id")
    sort_order = request.args.get("sort_order", "asc").upper()

    valid_sort_cols = {"wine_id", "wine_name", "category", "price", "quantity", "supplier_name", "created_at"}
    if sort_by not in valid_sort_cols:
        sort_by = "wine_id"
    if sort_order not in ("ASC", "DESC"):
        sort_order = "ASC"

    col_mapping = {
        "wine_id": "w.wine_id",
        "wine_name": "w.wine_name",
        "category": "w.category",
        "price": "w.price",
        "quantity": "w.quantity",
        "supplier_name": "s.supplier_name",
        "created_at": "w.created_at"
    }
    order_clause = f"{col_mapping[sort_by]} {sort_order}"

    sql = """
        SELECT 
            w.wine_id,
            w.wine_name,
            w.category,
            w.price,
            w.quantity,
            w.supplier_id,
            s.supplier_name,
            w.description,
            w.created_at,
            COALESCE(i.stock_quantity, w.quantity) AS stock_quantity,
            COALESCE(i.reorder_level, 10) AS reorder_level
        FROM wine w
        JOIN supplier s ON w.supplier_id = s.supplier_id
        LEFT JOIN inventory i ON w.wine_id = i.wine_id
        WHERE 1=1
    """
    params = []

    if search:
        sql += " AND (w.wine_name LIKE %s OR w.category LIKE %s OR s.supplier_name LIKE %s OR w.description LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if category and category.lower() != "all":
        sql += " AND w.category = %s"
        params.append(category)

    sql += f" ORDER BY {order_clause}"

    wines = execute_query(sql, params)
    return jsonify(wines)


@wine_bp.route("/<int:wine_id>", methods=["GET"])
def get_wine(wine_id):
    sql = """
        SELECT 
            w.wine_id,
            w.wine_name,
            w.category,
            w.price,
            w.quantity,
            w.supplier_id,
            s.supplier_name,
            w.description,
            w.created_at,
            COALESCE(i.stock_quantity, w.quantity) AS stock_quantity,
            COALESCE(i.reorder_level, 10) AS reorder_level
        FROM wine w
        JOIN supplier s ON w.supplier_id = s.supplier_id
        LEFT JOIN inventory i ON w.wine_id = i.wine_id
        WHERE w.wine_id = %s
    """
    wine = execute_query(sql, (wine_id,), fetch_one=True)
    if not wine:
        return jsonify({"success": False, "message": "Wine not found."}), 404
    return jsonify(wine)


@wine_bp.route("", methods=["POST"])
def add_wine():
    data = request.get_json() or {}
    wine_name = data.get("wine_name", "").strip()
    category = data.get("category", "").strip()
    price = data.get("price")
    quantity = data.get("quantity", 0)
    supplier_id = data.get("supplier_id")
    description = data.get("description", "").strip()

    if not wine_name:
        return jsonify({"success": False, "message": "Wine name is required."}), 400
    if not category:
        return jsonify({"success": False, "message": "Category is required."}), 400
    if price is None:
        return jsonify({"success": False, "message": "Price is required."}), 400

    try:
        price = float(price)
        if price < 0:
            return jsonify({"success": False, "message": "Price cannot be negative."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid price format."}), 400

    try:
        quantity = int(quantity)
        if quantity < 0:
            return jsonify({"success": False, "message": "Quantity cannot be negative."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid quantity format."}), 400

    if not supplier_id:
        return jsonify({"success": False, "message": "Supplier is required."}), 400

    # Verify supplier exists
    sup_check = "SELECT supplier_id FROM supplier WHERE supplier_id = %s"
    if not execute_query(sup_check, (supplier_id,), fetch_one=True):
        return jsonify({"success": False, "message": "Selected supplier does not exist."}), 400

    # Insert wine and inventory record in a single transaction
    with get_db() as db:
        cur = db.cursor()
        wine_sql = "INSERT INTO wine (wine_name, category, price, quantity, supplier_id, description) VALUES (%s, %s, %s, %s, %s, %s)"
        if not db.is_mysql:
            wine_sql = wine_sql.replace("%s", "?")
        cur.execute(wine_sql, (wine_name, category, price, quantity, supplier_id, description))
        new_wine_id = cur.lastrowid

        inv_sql = "INSERT INTO inventory (wine_id, stock_quantity, reorder_level) VALUES (%s, %s, 10)"
        if not db.is_mysql:
            inv_sql = inv_sql.replace("%s", "?")
        cur.execute(inv_sql, (new_wine_id, quantity))

        db.commit()

    return jsonify({
        "success": True,
        "message": "Wine added successfully.",
        "wine_id": new_wine_id
    }), 201


@wine_bp.route("/<int:wine_id>", methods=["PUT"])
def update_wine(wine_id):
    data = request.get_json() or {}
    wine_name = data.get("wine_name", "").strip()
    category = data.get("category", "").strip()
    price = data.get("price")
    quantity = data.get("quantity")
    supplier_id = data.get("supplier_id")
    description = data.get("description", "").strip()

    if not wine_name:
        return jsonify({"success": False, "message": "Wine name cannot be empty."}), 400
    if not category:
        return jsonify({"success": False, "message": "Category cannot be empty."}), 400

    try:
        price = float(price)
        if price < 0:
            return jsonify({"success": False, "message": "Price cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid price format."}), 400

    if quantity is not None:
        try:
            quantity = int(quantity)
            if quantity < 0:
                return jsonify({"success": False, "message": "Quantity cannot be negative."}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid quantity format."}), 400

    # Verify wine exists
    check_sql = "SELECT wine_id FROM wine WHERE wine_id = %s"
    if not execute_query(check_sql, (wine_id,), fetch_one=True):
        return jsonify({"success": False, "message": "Wine not found."}), 404

    # Verify supplier exists
    if supplier_id:
        sup_check = "SELECT supplier_id FROM supplier WHERE supplier_id = %s"
        if not execute_query(sup_check, (supplier_id,), fetch_one=True):
            return jsonify({"success": False, "message": "Selected supplier does not exist."}), 400

    with get_db() as db:
        cur = db.cursor()
        wine_sql = "UPDATE wine SET wine_name = %s, category = %s, price = %s, supplier_id = %s, description = %s WHERE wine_id = %s"
        params = [wine_name, category, price, supplier_id, description, wine_id]
        if not db.is_mysql:
            wine_sql = wine_sql.replace("%s", "?")
        cur.execute(wine_sql, params)

        if quantity is not None:
            # Sync quantity to wine and inventory
            q_sql = "UPDATE wine SET quantity = %s WHERE wine_id = %s"
            inv_sql = "UPDATE inventory SET stock_quantity = %s WHERE wine_id = %s"
            if not db.is_mysql:
                q_sql = q_sql.replace("%s", "?")
                inv_sql = inv_sql.replace("%s", "?")
            cur.execute(q_sql, (quantity, wine_id))
            cur.execute(inv_sql, (quantity, wine_id))

        db.commit()

    return jsonify({"success": True, "message": "Wine updated successfully."})


@wine_bp.route("/<int:wine_id>", methods=["DELETE"])
def delete_wine(wine_id):
    # Check if wine is referenced in order_details
    check_orders = "SELECT COUNT(*) AS cnt FROM order_details WHERE wine_id = %s"
    res = execute_query(check_orders, (wine_id,), fetch_one=True)
    if res and res.get("cnt", 0) > 0:
        return jsonify({
            "success": False,
            "message": "Wine cannot be deleted because orders are associated with this wine."
        }), 400

    with get_db() as db:
        cur = db.cursor()
        inv_del = "DELETE FROM inventory WHERE wine_id = %s"
        wine_del = "DELETE FROM wine WHERE wine_id = %s"
        if not db.is_mysql:
            inv_del = inv_del.replace("%s", "?")
            wine_del = wine_del.replace("%s", "?")
        cur.execute(inv_del, (wine_id,))
        cur.execute(wine_del, (wine_id,))
        db.commit()

    return jsonify({"success": True, "message": "Wine deleted successfully."})


@wine_bp.route("/import", methods=["POST"])
def upload_wines_csv():
    if "file" not in request.files:
        return jsonify({"success": False, "errors": ["No file uploaded."]}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "errors": ["File must be a .csv."]}), 400
    result = import_wines_csv(file.stream)
    return jsonify(result)


@wine_bp.route("/export", methods=["GET"])
@wine_bp.route("/export/csv", methods=["GET"])
def export_wines():
    sql = """
        SELECT 
            w.wine_id,
            w.wine_name,
            w.category,
            w.price,
            w.quantity,
            w.supplier_id,
            s.supplier_name,
            w.description,
            w.created_at
        FROM wine w
        JOIN supplier s ON w.supplier_id = s.supplier_id
        ORDER BY w.wine_id
    """
    wines = execute_query(sql)
    headers = ["wine_id", "wine_name", "category", "price", "quantity", "supplier_id", "supplier_name", "description", "created_at"]
    rows = [
        [
            w["wine_id"],
            w["wine_name"],
            w["category"],
            f"{float(w['price']):.2f}",
            w["quantity"],
            w["supplier_id"],
            w["supplier_name"],
            w["description"] or "",
            str(w["created_at"])
        ]
        for w in wines
    ]
    return generate_csv_response(headers, rows, "wines.csv")
