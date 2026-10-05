"""
Wines Management System - Supplier Routes
Handles Supplier CRUD, search, foreign key wine constraint verification on delete,
CSV import, and CSV export.
"""

from flask import Blueprint, request, jsonify
from db import get_db, execute_query
from utils.csv_utils import generate_csv_response, import_suppliers_csv

supplier_bp = Blueprint("suppliers", __name__, url_prefix="/api/suppliers")

@supplier_bp.route("", methods=["GET"])
def list_suppliers():
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "supplier_id")
    sort_order = request.args.get("sort_order", "asc").upper()

    valid_sort_cols = {"supplier_id", "supplier_name", "phone", "email", "created_at"}
    if sort_by not in valid_sort_cols:
        sort_by = "supplier_id"
    if sort_order not in ("ASC", "DESC"):
        sort_order = "ASC"

    sql = """
        SELECT 
            s.supplier_id,
            s.supplier_name,
            s.phone,
            s.email,
            s.address,
            s.created_at,
            COUNT(w.wine_id) AS wine_count
        FROM supplier s
        LEFT JOIN wine w ON s.supplier_id = w.supplier_id
        WHERE 1=1
    """
    params = []

    if search:
        sql += " AND (s.supplier_name LIKE %s OR s.phone LIKE %s OR s.email LIKE %s OR s.address LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    sql += f" GROUP BY s.supplier_id, s.supplier_name, s.phone, s.email, s.address, s.created_at ORDER BY s.{sort_by} {sort_order}"

    suppliers = execute_query(sql, params)
    return jsonify(suppliers)


@supplier_bp.route("/<int:supplier_id>", methods=["GET"])
def get_supplier(supplier_id):
    sql = """
        SELECT 
            s.supplier_id,
            s.supplier_name,
            s.phone,
            s.email,
            s.address,
            s.created_at,
            COUNT(w.wine_id) AS wine_count
        FROM supplier s
        LEFT JOIN wine w ON s.supplier_id = w.supplier_id
        WHERE s.supplier_id = %s
        GROUP BY s.supplier_id, s.supplier_name, s.phone, s.email, s.address, s.created_at
    """
    supplier = execute_query(sql, (supplier_id,), fetch_one=True)
    if not supplier:
        return jsonify({"success": False, "message": "Supplier not found."}), 404
    return jsonify(supplier)


@supplier_bp.route("", methods=["POST"])
def add_supplier():
    data = request.get_json() or {}
    name = data.get("supplier_name", "").strip()
    phone = data.get("phone", "").strip() or None
    email = data.get("email", "").strip() or None
    address = data.get("address", "").strip() or None

    if not name:
        return jsonify({"success": False, "message": "Supplier name is required."}), 400

    sql = "INSERT INTO supplier (supplier_name, phone, email, address) VALUES (%s, %s, %s, %s)"
    new_id = execute_query(sql, (name, phone, email, address), commit=True)
    return jsonify({
        "success": True,
        "message": "Supplier added successfully.",
        "supplier_id": new_id
    }), 201


@supplier_bp.route("/<int:supplier_id>", methods=["PUT"])
def update_supplier(supplier_id):
    data = request.get_json() or {}
    name = data.get("supplier_name", "").strip()
    phone = data.get("phone", "").strip() or None
    email = data.get("email", "").strip() or None
    address = data.get("address", "").strip() or None

    if not name:
        return jsonify({"success": False, "message": "Supplier name cannot be empty."}), 400

    check_sql = "SELECT supplier_id FROM supplier WHERE supplier_id = %s"
    if not execute_query(check_sql, (supplier_id,), fetch_one=True):
        return jsonify({"success": False, "message": "Supplier not found."}), 404

    sql = "UPDATE supplier SET supplier_name = %s, phone = %s, email = %s, address = %s WHERE supplier_id = %s"
    execute_query(sql, (name, phone, email, address, supplier_id), commit=True)
    return jsonify({"success": True, "message": "Supplier updated successfully."})


@supplier_bp.route("/<int:supplier_id>", methods=["DELETE"])
def delete_supplier(supplier_id):
    # Foreign key check: Do not delete if wines are linked
    wine_check = "SELECT COUNT(*) AS cnt FROM wine WHERE supplier_id = %s"
    res = execute_query(wine_check, (supplier_id,), fetch_one=True)
    if res and res.get("cnt", 0) > 0:
        return jsonify({
            "success": False,
            "message": "Cannot delete this supplier because wines are linked to it."
        }), 400

    sql = "DELETE FROM supplier WHERE supplier_id = %s"
    execute_query(sql, (supplier_id,), commit=True)
    return jsonify({"success": True, "message": "Supplier deleted successfully."})


@supplier_bp.route("/import", methods=["POST"])
def upload_suppliers_csv():
    if "file" not in request.files:
        return jsonify({"success": False, "errors": ["No file uploaded."]}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "errors": ["File must be a .csv."]}), 400
    result = import_suppliers_csv(file.stream)
    return jsonify(result)


@supplier_bp.route("/export", methods=["GET"])
@supplier_bp.route("/export/csv", methods=["GET"])
def export_suppliers():
    sql = "SELECT supplier_id, supplier_name, phone, email, address, created_at FROM supplier ORDER BY supplier_id"
    suppliers = execute_query(sql)
    headers = ["supplier_id", "supplier_name", "phone", "email", "address", "created_at"]
    rows = [
        [
            s["supplier_id"],
            s["supplier_name"],
            s["phone"] or "",
            s["email"] or "",
            s["address"] or "",
            str(s["created_at"])
        ]
        for s in suppliers
    ]
    return generate_csv_response(headers, rows, "suppliers.csv")
