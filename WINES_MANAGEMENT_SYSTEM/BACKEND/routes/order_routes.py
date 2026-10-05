"""
Wines Management System - Order Routes
Handles multi-item order placement with ACID transactions, stock deduction,
order retrieval with line-item breakdowns, payment status updates,
safe order cancellation/deletion, and CSV export.
"""

from flask import Blueprint, request, jsonify
from db import get_db, execute_query
from utils.csv_utils import generate_csv_response

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

@order_bp.route("", methods=["GET"])
def list_orders():
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("payment_status") or request.args.get("status", "").strip()
    sort_by = request.args.get("sort_by", "order_id")
    sort_order = request.args.get("sort_order", "desc").upper()

    valid_sort_cols = {"order_id", "customer_name", "order_date", "total_amount", "payment_status"}
    if sort_by not in valid_sort_cols:
        sort_by = "order_id"
    if sort_order not in ("ASC", "DESC"):
        sort_order = "DESC"

    col_mapping = {
        "order_id": "o.order_id",
        "customer_name": "c.customer_name",
        "order_date": "o.order_date",
        "total_amount": "o.total_amount",
        "payment_status": "o.payment_status"
    }

    sql = """
        SELECT 
            o.order_id,
            o.customer_id,
            c.customer_name,
            c.email AS customer_email,
            c.phone AS customer_phone,
            o.order_date,
            o.total_amount,
            o.payment_status,
            COUNT(od.order_detail_id) AS total_items,
            COUNT(od.order_detail_id) AS items_count
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        LEFT JOIN order_details od ON o.order_id = od.order_id
        WHERE 1=1
    """
    params = []

    if search:
        # Search by order_id or customer name
        if search.isdigit():
            sql += " AND (o.order_id = %s OR c.customer_name LIKE %s)"
            params.extend([int(search), f"%{search}%"])
        else:
            sql += " AND (c.customer_name LIKE %s OR o.payment_status LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

    if status_filter and status_filter.lower() != "all":
        sql += " AND o.payment_status = %s"
        params.append(status_filter)

    sql += f" GROUP BY o.order_id, o.customer_id, c.customer_name, c.email, c.phone, o.order_date, o.total_amount, o.payment_status ORDER BY {col_mapping[sort_by]} {sort_order}"

    orders = execute_query(sql, params)
    return jsonify(orders)


@order_bp.route("/<int:order_id>", methods=["GET"])
def get_order_details(order_id):
    order_sql = """
        SELECT 
            o.order_id,
            o.customer_id,
            c.customer_name,
            c.phone,
            c.email,
            c.address,
            c.phone AS customer_phone,
            c.email AS customer_email,
            c.address AS customer_address,
            o.order_date,
            o.total_amount,
            o.payment_status
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        WHERE o.order_id = %s
    """
    order = execute_query(order_sql, (order_id,), fetch_one=True)
    if not order:
        return jsonify({"success": False, "message": "Order not found."}), 404

    items_sql = """
        SELECT 
            od.order_detail_id,
            od.wine_id,
            w.wine_name,
            w.category,
            od.quantity,
            od.unit_price,
            (od.quantity * od.unit_price) AS subtotal,
            (od.quantity * od.unit_price) AS line_total
        FROM order_details od
        JOIN wine w ON od.wine_id = w.wine_id
        WHERE od.order_id = %s
        ORDER BY od.order_detail_id
    """
    items = execute_query(items_sql, (order_id,))
    order["items"] = items
    return jsonify(order)


@order_bp.route("", methods=["POST"])
def create_order():
    """
    Places a new sales order with multiple wine line items.
    ACID Transaction Implementation:
    1. Validates customer and items
    2. Checks real-time inventory for each item (prevents negative stock)
    3. Inserts into `orders`
    4. Inserts each item into `order_details` (excluding generated subtotal in MySQL)
    5. Deducts inventory.stock_quantity and wine.quantity
    6. Updates orders.total_amount
    7. Commits or Rollbacks on failure
    """
    data = request.get_json() or {}
    customer_id = data.get("customer_id")
    items = data.get("items", [])
    payment_status = data.get("payment_status", "Paid").strip()

    if not customer_id:
        return jsonify({"success": False, "message": "Customer is required."}), 400

    if not items or not isinstance(items, list):
        return jsonify({"success": False, "message": "Order must contain at least one item."}), 400

    if payment_status not in ("Pending", "Paid", "Cancelled"):
        payment_status = "Pending"

    with get_db() as db:
        cur = db.cursor()
        try:
            # 1. Verify customer exists
            cust_sql = "SELECT customer_id, customer_name FROM customer WHERE customer_id = %s" if db.is_mysql else "SELECT customer_id, customer_name FROM customer WHERE customer_id = ?"
            cur.execute(cust_sql, (customer_id,))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "Selected customer does not exist."}), 404

            # 2. Pre-validate stock for all items
            total_amount = 0.0
            validated_items = []

            for item in items:
                wine_id = item.get("wine_id")
                qty = item.get("quantity")

                if not wine_id or qty is None:
                    return jsonify({"success": False, "message": "Each item must have a wine and quantity."}), 400

                try:
                    qty = int(qty)
                    if qty <= 0:
                        return jsonify({"success": False, "message": "Quantity for each wine must be greater than zero."}), 400
                except (ValueError, TypeError):
                    return jsonify({"success": False, "message": "Invalid item quantity."}), 400

                # Query wine details and current stock
                w_sql = """
                    SELECT w.wine_id, w.wine_name, w.price, COALESCE(i.stock_quantity, w.quantity) AS current_stock
                    FROM wine w
                    LEFT JOIN inventory i ON w.wine_id = i.wine_id
                    WHERE w.wine_id = %s
                """ if db.is_mysql else """
                    SELECT w.wine_id, w.wine_name, w.price, COALESCE(i.stock_quantity, w.quantity) AS current_stock
                    FROM wine w
                    LEFT JOIN inventory i ON w.wine_id = i.wine_id
                    WHERE w.wine_id = ?
                """
                cur.execute(w_sql, (wine_id,))
                w_row = cur.fetchone()
                if not w_row:
                    return jsonify({"success": False, "message": f"Wine ID {wine_id} does not exist."}), 404

                w_id, w_name, price, current_stock = w_row[0], w_row[1], float(w_row[2]), int(w_row[3] or 0)

                if current_stock < qty:
                    return jsonify({
                        "success": False,
                        "message": f"Insufficient stock for '{w_name}'. Available: {current_stock}, Requested: {qty}."
                    }), 400

                subtotal = qty * price
                total_amount += subtotal
                validated_items.append({
                    "wine_id": w_id,
                    "wine_name": w_name,
                    "quantity": qty,
                    "unit_price": price,
                    "subtotal": subtotal
                })

            # 3. Insert into orders table
            ord_sql = "INSERT INTO orders (customer_id, total_amount, payment_status) VALUES (%s, %s, %s)" if db.is_mysql else "INSERT INTO orders (customer_id, total_amount, payment_status) VALUES (?, ?, ?)"
            cur.execute(ord_sql, (customer_id, total_amount, payment_status))
            order_id = cur.lastrowid

            # 4. Insert each order_detail and deduct inventory
            for v in validated_items:
                # In MySQL, subtotal is a STORED GENERATED column, so we omit subtotal in insert
                if db.is_mysql:
                    od_sql = "INSERT INTO order_details (order_id, wine_id, quantity, unit_price) VALUES (%s, %s, %s, %s)"
                    cur.execute(od_sql, (order_id, v["wine_id"], v["quantity"], v["unit_price"]))
                    # Update inventory
                    cur.execute("UPDATE inventory SET stock_quantity = stock_quantity - %s WHERE wine_id = %s", (v["quantity"], v["wine_id"]))
                    cur.execute("UPDATE wine SET quantity = quantity - %s WHERE wine_id = %s", (v["quantity"], v["wine_id"]))
                else:
                    od_sql = "INSERT INTO order_details (order_id, wine_id, quantity, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)"
                    cur.execute(od_sql, (order_id, v["wine_id"], v["quantity"], v["unit_price"], v["subtotal"]))
                    cur.execute("UPDATE inventory SET stock_quantity = stock_quantity - ? WHERE wine_id = ?", (v["quantity"], v["wine_id"]))
                    cur.execute("UPDATE wine SET quantity = quantity - ? WHERE wine_id = ?", (v["quantity"], v["wine_id"]))

            db.commit()

            return jsonify({
                "success": True,
                "message": f"Order #{order_id} created successfully.",
                "order_id": order_id,
                "total_amount": total_amount
            }), 201

        except Exception as e:
            db.rollback()
            return jsonify({
                "success": False,
                "message": f"Transaction failed and was rolled back: {str(e)}"
            }), 500


@order_bp.route("/<int:order_id>", methods=["PUT"])
def update_payment_status(order_id):
    data = request.get_json() or {}
    new_status = data.get("payment_status", "").strip()

    if new_status not in ("Pending", "Paid", "Cancelled"):
        return jsonify({"success": False, "message": "Payment status must be 'Pending', 'Paid', or 'Cancelled'."}), 400

    check_sql = "SELECT order_id FROM orders WHERE order_id = %s"
    if not execute_query(check_sql, (order_id,), fetch_one=True):
        return jsonify({"success": False, "message": "Order not found."}), 404

    sql = "UPDATE orders SET payment_status = %s WHERE order_id = %s"
    execute_query(sql, (new_status, order_id), commit=True)
    return jsonify({"success": True, "message": f"Order #{order_id} status updated to {new_status}."})


@order_bp.route("/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    check_sql = "SELECT order_id FROM orders WHERE order_id = %s"
    if not execute_query(check_sql, (order_id,), fetch_one=True):
        return jsonify({"success": False, "message": "Order not found."}), 404

    with get_db() as db:
        cur = db.cursor()
        del_details = "DELETE FROM order_details WHERE order_id = %s" if db.is_mysql else "DELETE FROM order_details WHERE order_id = ?"
        del_orders = "DELETE FROM orders WHERE order_id = %s" if db.is_mysql else "DELETE FROM orders WHERE order_id = ?"
        cur.execute(del_details, (order_id,))
        cur.execute(del_orders, (order_id,))
        db.commit()

    return jsonify({"success": True, "message": f"Order #{order_id} deleted successfully."})


@order_bp.route("/export", methods=["GET"])
@order_bp.route("/export/csv", methods=["GET"])
def export_orders():
    sql = """
        SELECT 
            o.order_id,
            o.customer_id,
            c.customer_name,
            o.order_date,
            o.total_amount,
            o.payment_status
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        ORDER BY o.order_id DESC
    """
    orders = execute_query(sql)
    headers = ["order_id", "customer_id", "customer_name", "order_date", "total_amount", "payment_status"]
    rows = [
        [
            o["order_id"],
            o["customer_id"],
            o["customer_name"],
            str(o["order_date"]),
            f"{float(o['total_amount']):.2f}",
            o["payment_status"]
        ]
        for o in orders
    ]
    return generate_csv_response(headers, rows, "orders.csv")


@order_bp.route("/details/export", methods=["GET"])
def export_order_details():
    sql = """
        SELECT 
            od.order_detail_id,
            od.order_id,
            c.customer_name,
            w.wine_name,
            w.category,
            od.quantity,
            od.unit_price,
            (od.quantity * od.unit_price) AS subtotal
        FROM order_details od
        JOIN orders o ON od.order_id = o.order_id
        JOIN customer c ON o.customer_id = c.customer_id
        JOIN wine w ON od.wine_id = w.wine_id
        ORDER BY od.order_detail_id ASC
    """
    details = execute_query(sql)
    headers = ["order_detail_id", "order_id", "customer_name", "wine_name", "category", "quantity", "unit_price", "subtotal"]
    rows = [
        [
            d["order_detail_id"],
            d["order_id"],
            d["customer_name"],
            d["wine_name"],
            d["category"],
            d["quantity"],
            f"{float(d['unit_price']):.2f}",
            f"{float(d['subtotal']):.2f}"
        ]
        for d in details
    ]
    return generate_csv_response(headers, rows, "order_details.csv")

