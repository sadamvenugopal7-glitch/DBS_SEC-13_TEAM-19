"""
Wines Management System - Customer Routes
Handles CRUD, search, foreign key order constraint verification on delete, CSV import, and CSV export.
"""

from flask import Blueprint, request, jsonify
from db import get_db, execute_query
from utils.csv_utils import generate_csv_response, import_customers_csv

customer_bp = Blueprint("customers", __name__, url_prefix="/api/customers")

@customer_bp.route("", methods=["GET"])
def list_customers():
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "customer_id")
    sort_order = request.args.get("sort_order", "asc").upper()

    valid_sort_cols = {"customer_id", "customer_name", "phone", "email", "created_at"}
    if sort_by not in valid_sort_cols:
        sort_by = "customer_id"
    if sort_order not in ("ASC", "DESC"):
        sort_order = "ASC"

    sql = """
        SELECT 
            c.customer_id, 
            c.customer_name, 
            c.phone, 
            c.email, 
            c.address, 
            c.created_at,
            COUNT(o.order_id) AS total_orders,
            COALESCE(SUM(o.total_amount), 0.0) AS total_spent
        FROM customer c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
    """
    params = []

    if search:
        sql += " WHERE c.customer_name LIKE %s OR c.phone LIKE %s OR c.email LIKE %s OR c.address LIKE %s"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    sql += f" GROUP BY c.customer_id, c.customer_name, c.phone, c.email, c.address, c.created_at ORDER BY c.{sort_by} {sort_order}"

    customers = execute_query(sql, params)
    return jsonify(customers)


@customer_bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    sql = "SELECT * FROM customer WHERE customer_id = %s"
    customer = execute_query(sql, (customer_id,), fetch_one=True)
    if not customer:
        return jsonify({"success": False, "message": "Customer not found."}), 404
    return jsonify(customer)


@customer_bp.route("", methods=["POST"])
def add_customer():
    data = request.get_json() or {}
    name = data.get("customer_name", "").strip()
    phone = data.get("phone", "").strip() or None
    email = data.get("email", "").strip() or None
    address = data.get("address", "").strip() or None

    if not name:
        return jsonify({"success": False, "message": "Customer name is required."}), 400

    sql = "INSERT INTO customer (customer_name, phone, email, address) VALUES (%s, %s, %s, %s)"
    new_id = execute_query(sql, (name, phone, email, address), commit=True)
    return jsonify({
        "success": True,
        "message": "Customer added successfully.",
        "customer_id": new_id
    }), 201


@customer_bp.route("/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    data = request.get_json() or {}
    name = data.get("customer_name", "").strip()
    phone = data.get("phone", "").strip() or None
    email = data.get("email", "").strip() or None
    address = data.get("address", "").strip() or None

    if not name:
        return jsonify({"success": False, "message": "Customer name cannot be empty."}), 400

    check_sql = "SELECT customer_id FROM customer WHERE customer_id = %s"
    if not execute_query(check_sql, (customer_id,), fetch_one=True):
        return jsonify({"success": False, "message": "Customer not found."}), 404

    sql = "UPDATE customer SET customer_name = %s, phone = %s, email = %s, address = %s WHERE customer_id = %s"
    execute_query(sql, (name, phone, email, address, customer_id), commit=True)
    return jsonify({"success": True, "message": "Customer updated successfully."})


@customer_bp.route("/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    # Check if customer has orders
    order_check = "SELECT COUNT(*) AS cnt FROM orders WHERE customer_id = %s"
    res = execute_query(order_check, (customer_id,), fetch_one=True)
    if res and res.get("cnt", 0) > 0:
        return jsonify({
            "success": False,
            "message": "Customer cannot be deleted because orders are associated with this customer."
        }), 400

    sql = "DELETE FROM customer WHERE customer_id = %s"
    execute_query(sql, (customer_id,), commit=True)
    return jsonify({"success": True, "message": "Customer deleted successfully."})


@customer_bp.route("/import", methods=["POST"])
def upload_customers_csv():
    if "file" not in request.files:
        return jsonify({"success": False, "errors": ["No file uploaded."]}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "errors": ["File must be a .csv."]}), 400
    result = import_customers_csv(file.stream)
    return jsonify(result)


@customer_bp.route("/export", methods=["GET"])
@customer_bp.route("/export/csv", methods=["GET"])
def export_customers():
    sql = "SELECT customer_id, customer_name, phone, email, address, created_at FROM customer ORDER BY customer_id"
    customers = execute_query(sql)
    headers = ["customer_id", "customer_name", "phone", "email", "address", "created_at"]
    rows = [[c["customer_id"], c["customer_name"], c["phone"] or "", c["email"] or "", c["address"] or "", str(c["created_at"])] for c in customers]
    return generate_csv_response(headers, rows, "customers.csv")
