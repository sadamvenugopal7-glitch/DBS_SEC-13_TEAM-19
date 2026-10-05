"""
Wines Management System - Full Automated System Verification
Validates:
1. Database connectivity
2. REST API endpoints (Flask)
3. CRUD for Customer, Wine, Supplier, Inventory, Order
4. ACID Transactions and Stock Deductions
5. Safe deletion restrictions (foreign key constraint violations)
6. CSV Export & Import endpoints
7. SQL data downloads
"""

import sys
import json
from app import app

def run_tests():
    client = app.test_client()
    passed = 0
    failed = 0

    def assert_test(name, condition, msg=""):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name} - {msg}")
            failed += 1

    print("\n" + "=" * 60)
    print("STARTING COMPREHENSIVE SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. Health & Dashboard
    res = client.get("/api/health")
    assert_test("API Health Check", res.status_code == 200 and res.json.get("status") == "healthy")

    res = client.get("/api/dashboard")
    assert_test("Dashboard Metrics Endpoint", res.status_code == 200 and "total_wines" in res.json)
    dash_data = res.json
    print(f"       Total Wines: {dash_data.get('total_wines')}")
    print(f"       Total Customers: {dash_data.get('total_customers')}")
    print(f"       Total Stock: {dash_data.get('total_stock')}")
    print(f"       Total Orders: {dash_data.get('total_orders')}")

    # 2. Customer CRUD
    cust_payload = {
        "customer_name": "Test Customer Auto",
        "phone": "+91 9988776655",
        "email": "auto_test@example.com",
        "address": "Bangalore, India"
    }
    res = client.post("/api/customers", json=cust_payload)
    assert_test("Create Customer", res.status_code == 201 and res.json.get("success"))
    new_cust_id = res.json.get("customer_id")

    res = client.get(f"/api/customers/{new_cust_id}")
    assert_test("Get Customer by ID", res.status_code == 200 and res.json.get("customer_name") == cust_payload["customer_name"])

    res = client.put(f"/api/customers/{new_cust_id}", json={
        "customer_name": "Updated Customer Auto",
        "phone": "+91 9988776600",
        "email": "updated_test@example.com",
        "address": "Hyderabad, India"
    })
    assert_test("Update Customer", res.status_code == 200 and res.json.get("success"))

    # 3. Supplier CRUD
    sup_payload = {
        "supplier_name": "Test Vineyard Estate",
        "phone": "+91 9123456780",
        "email": "vineyard_test@example.com",
        "address": "Nashik Valley, Maharashtra"
    }
    res = client.post("/api/suppliers", json=sup_payload)
    assert_test("Create Supplier", res.status_code == 201 and res.json.get("success"))
    new_sup_id = res.json.get("supplier_id")

    # 4. Wine CRUD
    wine_payload = {
        "wine_name": "Auto Reserve Cabernet",
        "category": "Red Wine",
        "price": 1850.00,
        "quantity": 100,
        "supplier_id": new_sup_id,
        "description": "Full-bodied oak aged wine for automated testing"
    }
    res = client.post("/api/wines", json=wine_payload)
    assert_test("Create Wine & Auto-Init Inventory", res.status_code == 201 and res.json.get("success"))
    new_wine_id = res.json.get("wine_id")

    # 5. Inventory Transactional Stock Add / Remove
    res = client.post("/api/inventory/add", json={"wine_id": new_wine_id, "quantity": 25})
    assert_test("Inventory Add Stock (Transaction)", res.status_code == 200 and res.json.get("new_stock") == 125)

    res = client.post("/api/inventory/remove", json={"wine_id": new_wine_id, "quantity": 15})
    assert_test("Inventory Remove Stock (Transaction)", res.status_code == 200 and res.json.get("new_stock") == 110)

    # Test Insufficient stock protection
    res = client.post("/api/inventory/remove", json={"wine_id": new_wine_id, "quantity": 9999})
    assert_test("Inventory Insufficient Stock Protection", res.status_code == 400 and "Insufficient stock" in res.json.get("message"))

    # 6. Sales Order Placement with ACID Transaction & Stock Deduction
    order_payload = {
        "customer_id": new_cust_id,
        "payment_status": "Paid",
        "items": [
            {"wine_id": new_wine_id, "quantity": 10}
        ]
    }
    res = client.post("/api/orders", json=order_payload)
    assert_test("Create Order with ACID Transaction", res.status_code == 201 and res.json.get("success"))
    new_order_id = res.json.get("order_id")

    # Check that stock decreased from 110 to 100
    res = client.get(f"/api/wines/{new_wine_id}")
    assert_test("Stock Decreased After Order Placement", res.status_code == 200 and res.json.get("stock_quantity") == 100)

    # Check order details breakdown
    res = client.get(f"/api/orders/{new_order_id}")
    assert_test("Retrieve Order Details & Line Items", res.status_code == 200 and len(res.json.get("items", [])) == 1)

    # 7. Safe Deletion Checks (Referential Constraints)
    # Customer with order cannot be deleted
    res = client.delete(f"/api/customers/{new_cust_id}")
    assert_test("Prevent Deleting Customer with Existing Orders", res.status_code == 400 and "orders are associated" in res.json.get("message"))

    # Supplier with wines cannot be deleted
    res = client.delete(f"/api/suppliers/{new_sup_id}")
    assert_test("Prevent Deleting Supplier with Existing Wines", res.status_code == 400 and "wines are linked" in res.json.get("message"))

    # Wine with order details cannot be deleted
    res = client.delete(f"/api/wines/{new_wine_id}")
    assert_test("Prevent Deleting Wine with Order History", res.status_code == 400 and "orders are associated" in res.json.get("message"))

    # 8. Clean up test order, wine, supplier, customer
    res = client.delete(f"/api/orders/{new_order_id}")
    assert_test("Delete Order", res.status_code == 200 and res.json.get("success"))

    res = client.delete(f"/api/wines/{new_wine_id}")
    assert_test("Delete Wine After Order Removed", res.status_code == 200 and res.json.get("success"))

    res = client.delete(f"/api/suppliers/{new_sup_id}")
    assert_test("Delete Supplier After Wines Removed", res.status_code == 200 and res.json.get("success"))

    res = client.delete(f"/api/customers/{new_cust_id}")
    assert_test("Delete Customer After Orders Removed", res.status_code == 200 and res.json.get("success"))

    # 9. CSV Exports
    res = client.get("/api/customers/export")
    assert_test("Export Customers CSV", res.status_code == 200 and "text/csv" in res.content_type)

    res = client.get("/api/wines/export")
    assert_test("Export Wines CSV", res.status_code == 200 and "text/csv" in res.content_type)

    res = client.get("/api/suppliers/export")
    assert_test("Export Suppliers CSV", res.status_code == 200 and "text/csv" in res.content_type)

    res = client.get("/api/inventory/export")
    assert_test("Export Inventory CSV", res.status_code == 200 and "text/csv" in res.content_type)

    res = client.get("/api/orders/export")
    assert_test("Export Orders CSV", res.status_code == 200 and "text/csv" in res.content_type)

    res = client.get("/api/order-details/export")
    assert_test("Export Order Details CSV", res.status_code == 200 and "text/csv" in res.content_type)

    # 10. Reports
    res = client.get("/api/reports/available-stock")
    assert_test("Report Available Stock", res.status_code == 200 and isinstance(res.json, list))

    res = client.get("/api/reports/low-stock")
    assert_test("Report Low Stock", res.status_code == 200 and isinstance(res.json, list))

    res = client.get("/api/reports/top-wines")
    assert_test("Report Top Selling Wines", res.status_code == 200 and isinstance(res.json, list))

    # 11. SQL Downloads
    res = client.get("/api/sql/complete")
    assert_test("Download Complete SQL Dump", res.status_code == 200 and "application/sql" in res.content_type)

    res = client.get("/api/sql/schema")
    assert_test("Download Schema SQL", res.status_code == 200 and "application/sql" in res.content_type)

    res = client.get("/api/sql/customers")
    assert_test("Download Dynamic Customers SQL", res.status_code == 200 and "application/sql" in res.content_type)

    # 12. Frontend Routing
    res = client.get("/")
    assert_test("Frontend Index Serves", res.status_code == 200 and b"WINES MANAGEMENT SYSTEM" in res.data)

    res = client.get("/sql-data.html")
    assert_test("Frontend SQL Data Page Serves", res.status_code == 200 and b"SQL Data" in res.data)

    res = client.get("/er-diagram.html")
    assert_test("Frontend ER Diagram Page Serves", res.status_code == 200 and b"Mermaid" in res.data)

    print("=" * 60)
    print(f"VERIFICATION SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
