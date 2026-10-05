"""
Wines Management System - Automated Verification & Function Test Suite
Tests all required operations: Database Models, CRUD, Transactions,
Stock Reconciliation, Safe Deletes, and Schema Consistency.
"""

import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base, SessionLocal
import models
import crud
import schemas

def run_tests():
    print("==================================================")
    print("RUNNING WINES MANAGEMENT SYSTEM VERIFICATION TESTS")
    print("==================================================")
    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"[PASS] {name}")
        else:
            print(f"[FAIL] {name} - {details}")

    # Ensure tables are created
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Test Seed Data exists or seed if empty
        wines_list = crud.get_wines(db, limit=5)
        if len(wines_list) == 0:
            print("[INFO] Database empty, seeding test supplier & wine...")
            sup = crud.create_supplier(db, schemas.SupplierCreate(
                supplier_name="Sula Vineyards Ltd",
                phone="+91-253-2297200",
                email="orders@sulawines.com",
                address="Nashik, Maharashtra"
            ))
            w = crud.create_wine(db, schemas.WineCreate(
                wine_name="Sula Rasa Cabernet Sauvignon",
                category="Red Wine",
                price=1850.00,
                quantity=45,
                supplier_id=sup.supplier_id
            ))
            w2 = crud.create_wine(db, schemas.WineCreate(
                wine_name="Sula Dindori Reserve Shiraz",
                category="Red Wine",
                price=1350.00,
                quantity=60,
                supplier_id=sup.supplier_id
            ))
            wines_list = crud.get_wines(db, limit=5)

        assert_test("1. Database Connection & Table Initialization", len(wines_list) > 0)

        # 2. Test GET Wines
        all_wines = crud.get_wines(db, limit=100)
        assert_test("2. GET Wines Catalog", len(all_wines) >= 1)

        # 3. Test Wine Search
        filtered = crud.get_wines(db, search="Sula")
        assert_test("3. Wine Search Query (WHERE ILIKE)", len(filtered) >= 1)

        # 4. Test Wine Category Filter
        cat_filtered = crud.get_wines(db, category="Red Wine")
        assert_test("4. Wine Category Filter (WHERE category)", len(cat_filtered) >= 1)

        # 5. Test POST Create Wine
        new_w = crud.create_wine(db, schemas.WineCreate(
            wine_name="Fratelli Sette Reserve 2026",
            category="Red Wine",
            price=2150.00,
            quantity=30,
            supplier_id=1
        ))
        assert_test("5. POST Create Wine", new_w.wine_id is not None)

        # 6. Test PUT Update Wine
        updated_w = crud.update_wine(db, new_w.wine_id, schemas.WineUpdate(price=2250.00))
        assert_test("6. PUT Update Wine Price", float(updated_w.price) == 2250.00)

        # 7. Test Customer Creation
        new_cust = crud.create_customer(db, schemas.CustomerCreate(
            customer_name="Sadam Venugopal",
            phone="+91-9876543210",
            email="sadam.venu@klu.ac.in",
            address="KL University Campus, Hyderabad"
        ))
        assert_test("7. POST Create Customer", new_cust.customer_id is not None)

        # 8. Test GET Customers
        cust_list = crud.get_customers(db, search="Sadam")
        assert_test("8. GET Customers with Search", len(cust_list) >= 1)

        # 9. Test Supplier Creation & Listing
        new_sup = crud.create_supplier(db, schemas.SupplierCreate(
            supplier_name="KRSMA Estates Hampi",
            phone="+91-83-94240500",
            email="cellar@krsmaestates.com",
            address="Hampi Hills, Karnataka"
        ))
        assert_test("9. POST Create Supplier", new_sup.supplier_id is not None)
        sups = crud.get_suppliers(db)
        assert_test("10. GET Suppliers List", len(sups) >= 1)

        # 11. Test Inventory Stock Management
        inv_item = crud.get_inventory_by_wine_id(db, new_w.wine_id) if hasattr(crud, "get_inventory_by_wine_id") else None
        inv_list = crud.get_inventory(db)
        assert_test("11. GET Inventory Records", len(inv_list) >= 1)

        # 12. Low-Stock Detection
        # Create a low stock item
        low_w = crud.create_wine(db, schemas.WineCreate(
            wine_name="Rare Vintage Port",
            category="Fortified Wine",
            price=3500.00,
            quantity=3,
            supplier_id=1
        ))
        crud.create_inventory(db, schemas.InventoryCreate(
            wine_id=low_w.wine_id,
            stock_quantity=2,
            reorder_level=10
        ))
        low_items = crud.get_inventory(db, low_stock_only=True)
        assert_test("12. Low Stock Detection Query", len(low_items) >= 1 and any(i["wine_id"] == low_w.wine_id for i in low_items))

        # 13. Test Order Creation within ACID Transaction
        target_wine = new_w
        inv_target = db.query(models.Inventory).filter(models.Inventory.wine_id == target_wine.wine_id).first()
        initial_stock = inv_target.stock_quantity if inv_target else target_wine.quantity

        order_res = crud.create_order_transaction(db, schemas.OrderCreate(
            customer_id=new_cust.customer_id,
            payment_status="Paid",
            items=[schemas.OrderItemCreate(wine_id=target_wine.wine_id, quantity=4)]
        ))
        assert_test("13. Order Creation via ACID Database Transaction", order_res["order_id"] is not None)

        # 14. Verify Inventory Stock Reduction
        db.refresh(inv_target)
        assert_test(
            "14. Automatic Inventory Stock Deduction Verification",
            inv_target.stock_quantity == initial_stock - 4,
            f"Expected {initial_stock - 4}, got {inv_target.stock_quantity}"
        )

        # 15. Transaction Rollback on Insufficient Stock
        oversell_failed = False
        try:
            crud.create_order_transaction(db, schemas.OrderCreate(
                customer_id=new_cust.customer_id,
                payment_status="Paid",
                items=[schemas.OrderItemCreate(wine_id=target_wine.wine_id, quantity=999999)]
            ))
        except Exception as exc:
            oversell_failed = True
        assert_test("15. ACID Transaction Rollback on Insufficient Stock", oversell_failed)

        # 16. Customer Safe Deletion Check (Customer with orders MUST NOT be deleted)
        customer_delete_blocked = False
        try:
            crud.delete_customer(db, new_cust.customer_id)
        except Exception as exc:
            customer_delete_blocked = "existing orders" in str(exc)
        assert_test("16. Customer Safe Delete Check (Referential Integrity Block)", customer_delete_blocked)

        # 17. GET Order Details
        order_details = crud.get_order_by_id(db, order_res["order_id"])
        assert_test("17. Order Details Breakdown Query", len(order_details["items"]) == 1)

        # 18. Dashboard Statistics Query
        stats = crud.get_dashboard_statistics(db)
        assert_test("18. Dashboard Statistics Aggregation Query", stats["total_wines"] >= 1 and stats["total_sales"] > 0)

        # 19. Category Distribution Aggregation
        cat_dist = crud.get_category_distribution(db)
        assert_test("19. Category Group By & Count Query", len(cat_dist) >= 1)

        # 20. Monthly Sales Aggregation
        monthly = crud.get_monthly_sales(db)
        assert_test("20. Monthly Sales Aggregation Query", len(monthly) >= 1)

        # 21. Delete Order with Stock Restoration
        stock_before_cancel = inv_target.stock_quantity
        crud.delete_order(db, order_res["order_id"])
        db.refresh(inv_target)
        assert_test("21. Delete Order & Stock Restoration", inv_target.stock_quantity == stock_before_cancel + 4)

        # 22. Now customer has no orders, deletion should succeed!
        clean_delete_success = crud.delete_customer(db, new_cust.customer_id)
        assert_test("22. Customer Deletion After Orders Resolved", clean_delete_success is True)

    finally:
        db.close()

    print("-" * 50)
    print(f"FINAL RESULT: {passed}/{total} TESTS PASSED ({round(passed/total*100)}%)")
    print("==================================================")
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
