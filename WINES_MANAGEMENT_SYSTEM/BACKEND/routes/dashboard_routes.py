"""
Wines Management System - Dashboard & Reports Routes
Provides real-time aggregated metrics from MySQL, Chart.js dataset feeds,
and 10 comprehensive academic analytical reports with CSV download capability.
"""

from flask import Blueprint, jsonify, request
from db import execute_query
from utils.csv_utils import generate_csv_response

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")

@dashboard_bp.route("/dashboard", methods=["GET"])
def get_dashboard_metrics():
    """Returns all 8 real-time core metrics and chart feeds from MySQL."""
    # 1. Counts
    wine_count = execute_query("SELECT COUNT(*) AS cnt FROM wine", fetch_one=True).get("cnt", 0)
    customer_count = execute_query("SELECT COUNT(*) AS cnt FROM customer", fetch_one=True).get("cnt", 0)
    supplier_count = execute_query("SELECT COUNT(*) AS cnt FROM supplier", fetch_one=True).get("cnt", 0)
    order_count = execute_query("SELECT COUNT(*) AS cnt FROM orders", fetch_one=True).get("cnt", 0)

    # 2. Stock metrics
    stock_res = execute_query("""
        SELECT 
            COALESCE(SUM(stock_quantity), 0) AS total_stock,
            COALESCE(SUM(CASE WHEN stock_quantity <= reorder_level AND stock_quantity > 0 THEN 1 ELSE 0 END), 0) AS low_stock_count,
            COALESCE(SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END), 0) AS out_of_stock_count,
            COALESCE(SUM(CASE WHEN stock_quantity > reorder_level THEN 1 ELSE 0 END), 0) AS in_stock_count
        FROM inventory
    """, fetch_one=True)

    # 3. Total sales (Paid orders)
    sales_res = execute_query("""
        SELECT COALESCE(SUM(total_amount), 0.0) AS total_sales
        FROM orders
        WHERE payment_status = 'Paid'
    """, fetch_one=True)

    # 4. Category breakdown for doughnut chart
    categories = execute_query("""
        SELECT category, COUNT(*) AS count
        FROM wine
        GROUP BY category
        ORDER BY count DESC
    """)

    # 5. Top 5 selling wines for bar chart
    top_wines = execute_query("""
        SELECT 
            w.wine_name,
            COALESCE(SUM(od.quantity), 0) AS total_sold,
            COALESCE(SUM(od.quantity * od.unit_price), 0.0) AS total_revenue
        FROM wine w
        LEFT JOIN order_details od ON w.wine_id = od.wine_id
        GROUP BY w.wine_id, w.wine_name
        ORDER BY total_sold DESC
        LIMIT 5
    """)

    # 6. Recent 5 orders for dashboard activity feed
    recent_orders = execute_query("""
        SELECT 
            o.order_id,
            c.customer_name,
            o.order_date,
            o.total_amount,
            o.payment_status
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        ORDER BY o.order_id DESC
        LIMIT 5
    """)

    return jsonify({
        "total_wines": wine_count,
        "total_customers": customer_count,
        "total_suppliers": supplier_count,
        "total_orders": order_count,
        "total_stock": int(stock_res.get("total_stock", 0)),
        "low_stock_count": int(stock_res.get("low_stock_count", 0)),
        "out_of_stock_count": int(stock_res.get("out_of_stock_count", 0)),
        "in_stock_count": int(stock_res.get("in_stock_count", 0)),
        "total_sales": float(sales_res.get("total_sales", 0.0)),
        "category_distribution": categories,
        "top_selling_wines": top_wines,
        "recent_orders": recent_orders
    })


# ==============================================================
# REPORT ENDPOINTS (10 Academic Reports)
# ==============================================================

@dashboard_bp.route("/reports/available-stock", methods=["GET"])
def report_available_stock():
    sql = """
        SELECT 
            w.wine_id,
            w.wine_name,
            w.category,
            w.price,
            i.stock_quantity,
            i.reorder_level,
            s.supplier_name,
            i.last_updated
        FROM inventory i
        JOIN wine w ON i.wine_id = w.wine_id
        JOIN supplier s ON w.supplier_id = s.supplier_id
        WHERE i.stock_quantity > 0
        ORDER BY i.stock_quantity DESC
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/low-stock", methods=["GET"])
def report_low_stock():
    sql = """
        SELECT 
            w.wine_id,
            w.wine_name,
            w.category,
            i.stock_quantity,
            i.reorder_level,
            w.price,
            s.supplier_name,
            s.phone AS supplier_phone,
            i.last_updated
        FROM inventory i
        JOIN wine w ON i.wine_id = w.wine_id
        JOIN supplier s ON w.supplier_id = s.supplier_id
        WHERE i.stock_quantity <= i.reorder_level AND i.stock_quantity > 0
        ORDER BY i.stock_quantity ASC
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/out-of-stock", methods=["GET"])
def report_out_of_stock():
    sql = """
        SELECT 
            w.wine_id,
            w.wine_name,
            w.category,
            i.stock_quantity,
            i.reorder_level,
            w.price,
            s.supplier_name,
            s.phone AS supplier_phone,
            s.email AS supplier_email,
            i.last_updated
        FROM inventory i
        JOIN wine w ON i.wine_id = w.wine_id
        JOIN supplier s ON w.supplier_id = s.supplier_id
        WHERE i.stock_quantity = 0
        ORDER BY w.wine_name ASC
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/customer-history", methods=["GET"])
def report_customer_history():
    customer_id = request.args.get("customer_id")
    sql = """
        SELECT 
            c.customer_id,
            c.customer_name,
            c.phone,
            c.email,
            o.order_id,
            o.order_date,
            o.total_amount,
            o.payment_status,
            COUNT(od.order_detail_id) AS items_count
        FROM customer c
        JOIN orders o ON c.customer_id = o.customer_id
        LEFT JOIN order_details od ON o.order_id = od.order_id
        WHERE 1=1
    """
    params = []
    if customer_id:
        sql += " AND c.customer_id = %s"
        params.append(customer_id)

    sql += " GROUP BY c.customer_id, c.customer_name, c.phone, c.email, o.order_id, o.order_date, o.total_amount, o.payment_status ORDER BY o.order_date DESC"
    return jsonify(execute_query(sql, params))


@dashboard_bp.route("/reports/sales", methods=["GET"])
def report_total_sales():
    sql = """
        SELECT 
            payment_status,
            COUNT(order_id) AS order_count,
            SUM(total_amount) AS total_revenue,
            AVG(total_amount) AS average_order_value
        FROM orders
        GROUP BY payment_status
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/sales-by-date", methods=["GET"])
def report_sales_by_date():
    sql = """
        SELECT 
            DATE(order_date) AS sale_date,
            COUNT(order_id) AS total_orders,
            SUM(total_amount) AS total_sales
        FROM orders
        WHERE payment_status = 'Paid'
        GROUP BY DATE(order_date)
        ORDER BY sale_date DESC
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/sales-by-wine", methods=["GET"])
def report_sales_by_wine():
    sql = """
        SELECT 
            w.wine_id,
            w.wine_name,
            w.category,
            w.price,
            COALESCE(SUM(od.quantity), 0) AS total_units_sold,
            COALESCE(SUM(od.quantity * od.unit_price), 0.0) AS total_revenue
        FROM wine w
        LEFT JOIN order_details od ON w.wine_id = od.wine_id
        GROUP BY w.wine_id, w.wine_name, w.category, w.price
        ORDER BY total_revenue DESC
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/sales-by-category", methods=["GET"])
def report_sales_by_category():
    sql = """
        SELECT 
            w.category,
            COUNT(DISTINCT w.wine_id) AS total_wines,
            COALESCE(SUM(od.quantity), 0) AS units_sold,
            COALESCE(SUM(od.quantity * od.unit_price), 0.0) AS revenue
        FROM wine w
        LEFT JOIN order_details od ON w.wine_id = od.wine_id
        GROUP BY w.category
        ORDER BY revenue DESC
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/supplier-wines", methods=["GET"])
def report_supplier_wines():
    sql = """
        SELECT 
            s.supplier_id,
            s.supplier_name,
            s.phone,
            s.email,
            COUNT(w.wine_id) AS total_wines_supplied,
            COALESCE(SUM(w.quantity), 0) AS total_stock_supplied
        FROM supplier s
        LEFT JOIN wine w ON s.supplier_id = w.supplier_id
        GROUP BY s.supplier_id, s.supplier_name, s.phone, s.email
        ORDER BY total_wines_supplied DESC
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/top-wines", methods=["GET"])
def report_top_wines():
    limit = request.args.get("limit", 10)
    try:
        limit = int(limit)
    except:
        limit = 10

    sql = f"""
        SELECT 
            w.wine_id,
            w.wine_name,
            w.category,
            w.price,
            s.supplier_name,
            SUM(od.quantity) AS total_quantity_sold,
            SUM(od.quantity * od.unit_price) AS total_sales_value
        FROM order_details od
        JOIN wine w ON od.wine_id = w.wine_id
        JOIN supplier s ON w.supplier_id = s.supplier_id
        GROUP BY w.wine_id, w.wine_name, w.category, w.price, s.supplier_name
        ORDER BY total_quantity_sold DESC
        LIMIT {limit}
    """
    return jsonify(execute_query(sql))


@dashboard_bp.route("/reports/export/<report_name>", methods=["GET"])
def export_report_csv(report_name):
    """Exports any analytical report directly to CSV."""
    if report_name == "available-stock":
        data = report_available_stock().get_json()
        headers = ["wine_id", "wine_name", "category", "price", "stock_quantity", "reorder_level", "supplier_name", "last_updated"]
        rows = [[d["wine_id"], d["wine_name"], d["category"], f"{float(d['price']):.2f}", d["stock_quantity"], d["reorder_level"], d["supplier_name"], str(d["last_updated"])] for d in data]
        return generate_csv_response(headers, rows, "report_available_stock.csv")

    elif report_name == "low-stock":
        data = report_low_stock().get_json()
        headers = ["wine_id", "wine_name", "category", "stock_quantity", "reorder_level", "price", "supplier_name", "supplier_phone", "last_updated"]
        rows = [[d["wine_id"], d["wine_name"], d["category"], d["stock_quantity"], d["reorder_level"], f"{float(d['price']):.2f}", d["supplier_name"], d["supplier_phone"] or "", str(d["last_updated"])] for d in data]
        return generate_csv_response(headers, rows, "report_low_stock.csv")

    elif report_name == "out-of-stock":
        data = report_out_of_stock().get_json()
        headers = ["wine_id", "wine_name", "category", "stock_quantity", "reorder_level", "price", "supplier_name", "supplier_phone", "supplier_email", "last_updated"]
        rows = [[d["wine_id"], d["wine_name"], d["category"], d["stock_quantity"], d["reorder_level"], f"{float(d['price']):.2f}", d["supplier_name"], d["supplier_phone"] or "", d["supplier_email"] or "", str(d["last_updated"])] for d in data]
        return generate_csv_response(headers, rows, "report_out_of_stock.csv")

    elif report_name == "customer-history":
        data = report_customer_history().get_json()
        headers = ["customer_id", "customer_name", "phone", "email", "order_id", "order_date", "total_amount", "payment_status", "items_count"]
        rows = [[d["customer_id"], d["customer_name"], d["phone"] or "", d["email"] or "", d["order_id"], str(d["order_date"]), f"{float(d['total_amount']):.2f}", d["payment_status"], d["items_count"]] for d in data]
        return generate_csv_response(headers, rows, "report_customer_orders.csv")

    elif report_name == "sales-by-date":
        data = report_sales_by_date().get_json()
        headers = ["sale_date", "total_orders", "total_sales"]
        rows = [[str(d["sale_date"]), d["total_orders"], f"{float(d['total_sales']):.2f}"] for d in data]
        return generate_csv_response(headers, rows, "report_sales_by_date.csv")

    elif report_name == "sales-by-wine":
        data = report_sales_by_wine().get_json()
        headers = ["wine_id", "wine_name", "category", "price", "total_units_sold", "total_revenue"]
        rows = [[d["wine_id"], d["wine_name"], d["category"], f"{float(d['price']):.2f}", d["total_units_sold"], f"{float(d['total_revenue']):.2f}"] for d in data]
        return generate_csv_response(headers, rows, "report_sales_by_wine.csv")

    elif report_name == "sales-by-category":
        data = report_sales_by_category().get_json()
        headers = ["category", "total_wines", "units_sold", "revenue"]
        rows = [[d["category"], d["total_wines"], d["units_sold"], f"{float(d['revenue']):.2f}"] for d in data]
        return generate_csv_response(headers, rows, "report_sales_by_category.csv")

    elif report_name == "supplier-wines":
        data = report_supplier_wines().get_json()
        headers = ["supplier_id", "supplier_name", "phone", "email", "total_wines_supplied", "total_stock_supplied"]
        rows = [[d["supplier_id"], d["supplier_name"], d["phone"] or "", d["email"] or "", d["total_wines_supplied"], d["total_stock_supplied"]] for d in data]
        return generate_csv_response(headers, rows, "report_supplier_wines.csv")

    elif report_name == "top-wines":
        data = report_top_wines().get_json()
        headers = ["wine_id", "wine_name", "category", "price", "supplier_name", "total_quantity_sold", "total_sales_value"]
        rows = [[d["wine_id"], d["wine_name"], d["category"], f"{float(d['price']):.2f}", d["supplier_name"], d["total_quantity_sold"], f"{float(d['total_sales_value']):.2f}"] for d in data]
        return generate_csv_response(headers, rows, "report_top_selling_wines.csv")

    else:
        # Default total sales summary
        data = report_total_sales().get_json()
        headers = ["payment_status", "order_count", "total_revenue", "average_order_value"]
        rows = [[d["payment_status"], d["order_count"], f"{float(d['total_revenue']):.2f}", f"{float(d['average_order_value']):.2f}"] for d in data]
        return generate_csv_response(headers, rows, "report_sales_summary.csv")
