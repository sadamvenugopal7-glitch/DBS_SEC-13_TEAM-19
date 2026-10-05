"""
Wines Management System - Flask Application Entrypoint
Academic DBMS Engineering Project - Team 19, Section 3
Serves REST API, dynamic SQL/CSV stream downloads, and responsive frontend dashboard.
"""

import os
import sys
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS

# Add backend directory to system path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import Config
from db import get_db, execute_query
from routes.customer_routes import customer_bp
from routes.wine_routes import wine_bp
from routes.supplier_routes import supplier_bp
from routes.inventory_routes import inventory_bp
from routes.order_routes import order_bp, export_order_details
from routes.dashboard_routes import dashboard_bp
from utils.sql_export import get_sql_file, export_table_sql

# Directory paths
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config.from_object(Config)

# Enable CORS for cross-origin integration
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register REST API Blueprints
app.register_blueprint(customer_bp)
app.register_blueprint(wine_bp)
app.register_blueprint(supplier_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(order_bp)
app.register_blueprint(dashboard_bp)

# Alias for order details export
@app.route("/api/order-details/export", methods=["GET"])
def api_order_details_export():
    return export_order_details()

# ==============================================================
# SQL DATA DOWNLOAD ROUTES (MySQL Workbench & Migration Dumps)
# ==============================================================
@app.route("/api/sql/complete", methods=["GET"])
def download_complete_sql():
    return get_sql_file("complete_database.sql", "complete_database.sql")

@app.route("/api/sql/schema", methods=["GET"])
def download_schema_sql():
    return get_sql_file("02_create_tables.sql", "schema_tables.sql")

@app.route("/api/sql/sample-data", methods=["GET"])
def download_sample_data_sql():
    return get_sql_file("03_insert_sample_data.sql", "sample_data.sql")

@app.route("/api/sql/customers", methods=["GET"])
def download_customers_sql():
    return export_table_sql("customer", "customers_data.sql")

@app.route("/api/sql/wines", methods=["GET"])
def download_wines_sql():
    return export_table_sql("wine", "wines_data.sql")

@app.route("/api/sql/suppliers", methods=["GET"])
def download_suppliers_sql():
    return export_table_sql("supplier", "suppliers_data.sql")

@app.route("/api/sql/inventory", methods=["GET"])
def download_inventory_sql():
    return export_table_sql("inventory", "inventory_data.sql")

@app.route("/api/sql/orders", methods=["GET"])
def download_orders_sql():
    return export_table_sql("orders", "orders_data.sql")

@app.route("/api/sql/order-details", methods=["GET"])
def download_order_details_sql():
    return export_table_sql("order_details", "order_details_data.sql")

# ==============================================================
# HEALTH CHECK
# ==============================================================
@app.route("/api/health", methods=["GET"])
def health_check():
    db_type = "MySQL 8.x" if Config.DB_PASSWORD else "SQLite (Fallback/Demo)"
    return jsonify({
        "status": "healthy",
        "project": "WINES MANAGEMENT SYSTEM",
        "team": "Team 19, Section 3",
        "database": Config.DB_NAME,
        "engine": db_type
    })

# ==============================================================
# FRONTEND STATIC ROUTING
# ==============================================================
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/sql-data.html")
@app.route("/export.html")
def serve_sql_data():
    if os.path.exists(os.path.join(FRONTEND_DIR, "sql-data.html")):
        return send_from_directory(FRONTEND_DIR, "sql-data.html")
    return send_from_directory(FRONTEND_DIR, "export.html")

@app.route("/er-diagram.html")
@app.route("/erd.html")
def serve_er_diagram():
    if os.path.exists(os.path.join(FRONTEND_DIR, "er-diagram.html")):
        return send_from_directory(FRONTEND_DIR, "er-diagram.html")
    return send_from_directory(FRONTEND_DIR, "erd.html")

@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

# ==============================================================
# GLOBAL ERROR HANDLERS
# ==============================================================
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"success": False, "message": str(e.description if hasattr(e, 'description') else "Bad request.")}), 400

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "API endpoint not found."}), 404
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Internal server error occurred."}), 500

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("[*] WINES MANAGEMENT SYSTEM - Flask Server Starting")
    print("    Academic DBMS Project | Team 19, Section 3")
    print(f"    Database: {Config.DB_NAME} on {Config.DB_HOST}:{Config.DB_PORT}")
    print("    Application URL: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
