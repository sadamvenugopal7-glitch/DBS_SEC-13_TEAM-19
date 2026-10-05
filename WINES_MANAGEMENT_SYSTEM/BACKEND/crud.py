"""
Wines Management System - Database CRUD Operations
Encapsulates all database interactions, SQL queries, joins, aggregations,
safe foreign-key handling, and ACID transaction logic.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc, asc, text
from fastapi import HTTPException, status

import models
import schemas


# =====================================================================
# WINE CRUD OPERATIONS
# =====================================================================
def get_wines(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = "wine_id",
    sort_order: Optional[str] = "asc",
    skip: int = 0,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieve wines with backend search, filtering, and sorting."""
    query = db.query(models.Wine).options(joinedload(models.Wine.supplier))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Wine.wine_name.ilike(term),
                models.Wine.category.ilike(term)
            )
        )

    if category and category.strip() and category != "All":
        query = query.filter(models.Wine.category == category.strip())

    # Sorting
    sort_column = getattr(models.Wine, sort_by, models.Wine.wine_id)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    wines = query.offset(skip).limit(limit).all()

    result = []
    for w in wines:
        result.append({
            "wine_id": w.wine_id,
            "wine_name": w.wine_name,
            "category": w.category,
            "price": float(w.price),
            "quantity": w.quantity,
            "supplier_id": w.supplier_id,
            "supplier_name": w.supplier.supplier_name if w.supplier else "N/A",
            "created_at": w.created_at
        })
    return result


def get_wine_by_id(db: Session, wine_id: int) -> Optional[models.Wine]:
    return db.query(models.Wine).filter(models.Wine.wine_id == wine_id).first()


def create_wine(db: Session, wine_data: schemas.WineCreate) -> models.Wine:
    db_wine = models.Wine(
        wine_name=wine_data.wine_name,
        category=wine_data.category,
        price=wine_data.price,
        quantity=wine_data.quantity,
        supplier_id=wine_data.supplier_id
    )
    db.add(db_wine)
    db.flush()

    # Automatically ensure inventory record exists for the new wine
    db_inventory = models.Inventory(
        wine_id=db_wine.wine_id,
        stock_quantity=wine_data.quantity,
        reorder_level=10
    )
    db.add(db_inventory)
    db.commit()
    db.refresh(db_wine)
    return db_wine


def update_wine(db: Session, wine_id: int, wine_data: schemas.WineUpdate) -> models.Wine:
    db_wine = get_wine_by_id(db, wine_id)
    if not db_wine:
        raise HTTPException(status_code=404, detail="Wine not found.")

    update_dict = wine_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_wine, key, value)

    # Sync inventory stock if quantity was updated
    if "quantity" in update_dict:
        inv = db.query(models.Inventory).filter(models.Inventory.wine_id == wine_id).first()
        if inv:
            inv.stock_quantity = update_dict["quantity"]

    db.commit()
    db.refresh(db_wine)
    return db_wine


def delete_wine(db: Session, wine_id: int) -> bool:
    db_wine = get_wine_by_id(db, wine_id)
    if not db_wine:
        raise HTTPException(status_code=404, detail="Wine not found.")

    # Check if this wine is referenced in order details (foreign key dependency)
    has_orders = db.query(models.OrderDetail).filter(models.OrderDetail.wine_id == wine_id).first()
    if has_orders:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete this wine because existing sales order details depend on it."
        )

    db.delete(db_wine)
    db.commit()
    return True


# =====================================================================
# CUSTOMER CRUD OPERATIONS
# =====================================================================
def get_customers(
    db: Session,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Dict[str, Any]]:
    query = db.query(models.Customer)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Customer.customer_name.ilike(term),
                models.Customer.phone.ilike(term),
                models.Customer.email.ilike(term),
                models.Customer.address.ilike(term)
            )
        )

    customers = query.order_by(asc(models.Customer.customer_id)).offset(skip).limit(limit).all()

    # Aggregate order stats for each customer
    result = []
    for c in customers:
        order_stats = db.query(
            func.count(models.Order.order_id).label("order_count"),
            func.coalesce(func.sum(models.Order.total_amount), 0).label("total_spent")
        ).filter(models.Order.customer_id == c.customer_id).first()

        result.append({
            "customer_id": c.customer_id,
            "customer_name": c.customer_name,
            "phone": c.phone or "N/A",
            "email": c.email or "N/A",
            "address": c.address or "N/A",
            "total_orders": order_stats.order_count if order_stats else 0,
            "total_spent": float(order_stats.total_spent) if order_stats else 0.0,
            "created_at": c.created_at
        })
    return result


def get_customer_by_id(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()


def create_customer(db: Session, customer_data: schemas.CustomerCreate) -> models.Customer:
    db_customer = models.Customer(**customer_data.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def update_customer(db: Session, customer_id: int, customer_data: schemas.CustomerUpdate) -> models.Customer:
    db_customer = get_customer_by_id(db, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    for key, value in customer_data.model_dump(exclude_unset=True).items():
        setattr(db_customer, key, value)

    db.commit()
    db.refresh(db_customer)
    return db_customer


def delete_customer(db: Session, customer_id: int) -> bool:
    """Safe Customer Deletion: Checks whether customer has existing orders before deletion."""
    db_customer = get_customer_by_id(db, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Check for existing orders
    existing_orders = db.query(models.Order).filter(models.Order.customer_id == customer_id).count()
    if existing_orders > 0:
        raise HTTPException(
            status_code=400,
            detail="This customer has existing orders and cannot be deleted directly."
        )

    db.delete(db_customer)
    db.commit()
    return True


# =====================================================================
# SUPPLIER CRUD OPERATIONS
# =====================================================================
def get_suppliers(
    db: Session,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Dict[str, Any]]:
    query = db.query(models.Supplier)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Supplier.supplier_name.ilike(term),
                models.Supplier.phone.ilike(term),
                models.Supplier.email.ilike(term),
                models.Supplier.address.ilike(term)
            )
        )

    suppliers = query.order_by(asc(models.Supplier.supplier_id)).offset(skip).limit(limit).all()

    result = []
    for s in suppliers:
        wine_count = db.query(models.Wine).filter(models.Wine.supplier_id == s.supplier_id).count()
        result.append({
            "supplier_id": s.supplier_id,
            "supplier_name": s.supplier_name,
            "phone": s.phone or "N/A",
            "email": s.email or "N/A",
            "address": s.address or "N/A",
            "wine_count": wine_count,
            "created_at": s.created_at
        })
    return result


def get_supplier_by_id(db: Session, supplier_id: int) -> Optional[models.Supplier]:
    return db.query(models.Supplier).filter(models.Supplier.supplier_id == supplier_id).first()


def create_supplier(db: Session, supplier_data: schemas.SupplierCreate) -> models.Supplier:
    db_supplier = models.Supplier(**supplier_data.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def update_supplier(db: Session, supplier_id: int, supplier_data: schemas.SupplierUpdate) -> models.Supplier:
    db_supplier = get_supplier_by_id(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")

    for key, value in supplier_data.model_dump(exclude_unset=True).items():
        setattr(db_supplier, key, value)

    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def delete_supplier(db: Session, supplier_id: int) -> bool:
    db_supplier = get_supplier_by_id(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")

    db.delete(db_supplier)
    db.commit()
    return True


# =====================================================================
# INVENTORY CRUD OPERATIONS
# =====================================================================
def get_inventory(
    db: Session,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[Dict[str, Any]]:
    query = db.query(models.Inventory).join(models.Wine)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Wine.wine_name.ilike(term),
                models.Wine.category.ilike(term)
            )
        )

    if low_stock_only:
        query = query.filter(models.Inventory.stock_quantity <= models.Inventory.reorder_level)

    items = query.order_by(asc(models.Inventory.stock_quantity)).offset(skip).limit(limit).all()

    result = []
    for item in items:
        status_label = "LOW STOCK" if item.stock_quantity <= item.reorder_level else "AVAILABLE"
        result.append({
            "inventory_id": item.inventory_id,
            "wine_id": item.wine_id,
            "wine_name": item.wine.wine_name if item.wine else "Unknown Wine",
            "category": item.wine.category if item.wine else "N/A",
            "price": float(item.wine.price) if item.wine else 0.0,
            "stock_quantity": item.stock_quantity,
            "reorder_level": item.reorder_level,
            "status": status_label,
            "last_updated": item.last_updated
        })
    return result


def get_inventory_by_id(db: Session, inventory_id: int) -> Optional[models.Inventory]:
    return db.query(models.Inventory).filter(models.Inventory.inventory_id == inventory_id).first()


def create_inventory(db: Session, inv_data: schemas.InventoryCreate) -> models.Inventory:
    # Check if wine exists
    wine = get_wine_by_id(db, inv_data.wine_id)
    if not wine:
        raise HTTPException(status_code=404, detail=f"Wine with ID {inv_data.wine_id} does not exist.")

    # Check if inventory already exists for this wine
    existing = db.query(models.Inventory).filter(models.Inventory.wine_id == inv_data.wine_id).first()
    if existing:
        existing.stock_quantity = inv_data.stock_quantity
        existing.reorder_level = inv_data.reorder_level
        wine.quantity = inv_data.stock_quantity
        db.commit()
        db.refresh(existing)
        return existing

    db_inv = models.Inventory(**inv_data.model_dump())
    db.add(db_inv)
    wine.quantity = inv_data.stock_quantity
    db.commit()
    db.refresh(db_inv)
    return db_inv


def update_inventory(db: Session, inventory_id: int, inv_data: schemas.InventoryUpdate) -> models.Inventory:
    db_inv = get_inventory_by_id(db, inventory_id)
    if not db_inv:
        raise HTTPException(status_code=404, detail="Inventory record not found.")

    for key, value in inv_data.model_dump(exclude_unset=True).items():
        setattr(db_inv, key, value)

    # Sync wine table quantity if stock_quantity changed
    if inv_data.stock_quantity is not None:
        wine = get_wine_by_id(db, db_inv.wine_id)
        if wine:
            wine.quantity = inv_data.stock_quantity

    db.commit()
    db.refresh(db_inv)
    return db_inv


def delete_inventory(db: Session, inventory_id: int) -> bool:
    db_inv = get_inventory_by_id(db, inventory_id)
    if not db_inv:
        raise HTTPException(status_code=404, detail="Inventory record not found.")

    db.delete(db_inv)
    db.commit()
    return True


# =====================================================================
# ORDER CRUD OPERATIONS WITH ACID DATABASE TRANSACTIONS
# =====================================================================
def create_order_transaction(db: Session, order_in: schemas.OrderCreate) -> Dict[str, Any]:
    """
    Executes a complete ACID Transaction:
    1. Verifies customer exists.
    2. Inserts Order record with initial amount 0.00.
    3. For each requested wine:
       - Validates wine existence.
       - Validates available inventory stock.
       - Deducts stock from inventory and wine tables.
       - Inserts OrderDetail record.
       - Accumulates total line amount.
    4. Updates final Order total_amount.
    5. Commits transaction if all operations succeed; rollbacks on any failure.
    """
    customer = get_customer_by_id(db, order_in.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID {order_in.customer_id} does not exist.")

    if not order_in.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one wine item.")

    try:
        # Start Transaction
        db_order = models.Order(
            customer_id=order_in.customer_id,
            order_date=datetime.now(),
            total_amount=0.00,
            payment_status=order_in.payment_status or "Paid"
        )
        db.add(db_order)
        db.flush()  # Obtain order_id

        total_amount = 0.00

        for item in order_in.items:
            wine = get_wine_by_id(db, item.wine_id)
            if not wine:
                raise HTTPException(status_code=404, detail=f"Wine ID {item.wine_id} not found.")

            # Check inventory stock
            inv = db.query(models.Inventory).filter(models.Inventory.wine_id == item.wine_id).first()
            current_stock = inv.stock_quantity if inv else wine.quantity

            if current_stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{wine.wine_name}'. Available: {current_stock}, Requested: {item.quantity}."
                )

            # Deduct stock
            if inv:
                inv.stock_quantity -= item.quantity
            wine.quantity = max(0, wine.quantity - item.quantity)

            unit_price = float(wine.price)
            line_total = unit_price * item.quantity
            total_amount += line_total

            # Create OrderDetail
            order_detail = models.OrderDetail(
                order_id=db_order.order_id,
                wine_id=item.wine_id,
                quantity=item.quantity,
                unit_price=unit_price
            )
            db.add(order_detail)

        # Update order total
        db_order.total_amount = total_amount
        db.commit()
        db.refresh(db_order)

        return {
            "order_id": db_order.order_id,
            "customer_id": db_order.customer_id,
            "customer_name": customer.customer_name,
            "order_date": db_order.order_date,
            "total_amount": float(db_order.total_amount),
            "payment_status": db_order.payment_status,
            "message": "Order placed successfully within database transaction."
        }

    except Exception as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=500,
            detail=f"Transaction rolled back due to database error: {str(exc)}"
        )


def get_orders(
    db: Session,
    search: Optional[str] = None,
    payment_status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Dict[str, Any]]:
    query = db.query(models.Order).join(models.Customer)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Customer.customer_name.ilike(term),
                models.Order.payment_status.ilike(term)
            )
        )

    if payment_status and payment_status.strip() and payment_status != "All":
        query = query.filter(models.Order.payment_status == payment_status.strip())

    if start_date:
        query = query.filter(models.Order.order_date >= start_date)
    if end_date:
        query = query.filter(models.Order.order_date <= end_date + " 23:59:59")

    orders = query.order_by(desc(models.Order.order_date)).offset(skip).limit(limit).all()

    result = []
    for o in orders:
        details_count = db.query(models.OrderDetail).filter(models.OrderDetail.order_id == o.order_id).count()
        result.append({
            "order_id": o.order_id,
            "customer_id": o.customer_id,
            "customer_name": o.customer.customer_name if o.customer else "Unknown Customer",
            "order_date": o.order_date,
            "total_amount": float(o.total_amount),
            "payment_status": o.payment_status,
            "items_count": details_count
        })
    return result


def get_order_by_id(db: Session, order_id: int) -> Dict[str, Any]:
    order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    details = db.query(models.OrderDetail).filter(models.OrderDetail.order_id == order_id).all()

    items = []
    for d in details:
        wine = db.query(models.Wine).filter(models.Wine.wine_id == d.wine_id).first()
        items.append({
            "order_detail_id": d.order_detail_id,
            "order_id": d.order_id,
            "wine_id": d.wine_id,
            "wine_name": wine.wine_name if wine else "Unknown",
            "category": wine.category if wine else "N/A",
            "quantity": d.quantity,
            "unit_price": float(d.unit_price),
            "line_total": float(d.quantity * d.unit_price)
        })

    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "customer_name": order.customer.customer_name if order.customer else "Unknown",
        "customer_phone": order.customer.phone if order.customer else "N/A",
        "customer_email": order.customer.email if order.customer else "N/A",
        "customer_address": order.customer.address if order.customer else "N/A",
        "order_date": order.order_date,
        "total_amount": float(order.total_amount),
        "payment_status": order.payment_status,
        "items": items
    }


def delete_order(db: Session, order_id: int) -> bool:
    order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Restoring stock on order cancellation/deletion
    details = db.query(models.OrderDetail).filter(models.OrderDetail.order_id == order_id).all()
    for d in details:
        inv = db.query(models.Inventory).filter(models.Inventory.wine_id == d.wine_id).first()
        if inv:
            inv.stock_quantity += d.quantity
        wine = get_wine_by_id(db, d.wine_id)
        if wine:
            wine.quantity += d.quantity

    db.delete(order)
    db.commit()
    return True


# =====================================================================
# DASHBOARD & STATISTICS QUERIES
# =====================================================================
def get_dashboard_statistics(db: Session) -> Dict[str, Any]:
    total_wines = db.query(func.count(models.Wine.wine_id)).scalar() or 0
    total_customers = db.query(func.count(models.Customer.customer_id)).scalar() or 0
    total_suppliers = db.query(func.count(models.Supplier.supplier_id)).scalar() or 0
    total_orders = db.query(func.count(models.Order.order_id)).scalar() or 0

    total_stock = db.query(func.sum(models.Inventory.stock_quantity)).scalar()
    if total_stock is None:
        total_stock = db.query(func.sum(models.Wine.quantity)).scalar() or 0

    total_sales = db.query(func.sum(models.Order.total_amount)).filter(models.Order.payment_status == "Paid").scalar() or 0.0

    low_stock_count = db.query(func.count(models.Inventory.inventory_id)).filter(
        models.Inventory.stock_quantity <= models.Inventory.reorder_level
    ).scalar() or 0

    return {
        "total_wines": total_wines,
        "total_customers": total_customers,
        "total_suppliers": total_suppliers,
        "total_orders": total_orders,
        "total_stock": int(total_stock),
        "total_sales": round(float(total_sales), 2),
        "low_stock_count": low_stock_count
    }


def get_category_distribution(db: Session) -> List[Dict[str, Any]]:
    results = db.query(
        models.Wine.category,
        func.count(models.Wine.wine_id).label("wine_count"),
        func.coalesce(func.sum(models.Wine.quantity), 0).label("stock_count")
    ).group_by(models.Wine.category).all()

    return [{"category": r.category, "count": r.wine_count, "stock": int(r.stock_count)} for r in results]


def get_monthly_sales(db: Session) -> List[Dict[str, Any]]:
    # Date formatting for MySQL or SQLite
    orders = db.query(models.Order).order_by(asc(models.Order.order_date)).all()
    monthly: Dict[str, Dict[str, Any]] = {}

    for o in orders:
        if o.order_date:
            m_str = o.order_date.strftime("%Y-%m")
            if m_str not in monthly:
                monthly[m_str] = {"month": m_str, "revenue": 0.0, "orders": 0}
            if o.payment_status == "Paid":
                monthly[m_str]["revenue"] += float(o.total_amount)
            monthly[m_str]["orders"] += 1

    return list(monthly.values())


def get_stock_chart_data(db: Session, limit: int = 15) -> List[Dict[str, Any]]:
    items = db.query(models.Inventory).join(models.Wine).order_by(
        asc(models.Inventory.stock_quantity)
    ).limit(limit).all()

    return [{
        "wine_name": item.wine.wine_name if item.wine else "Wine",
        "stock": item.stock_quantity,
        "reorder_level": item.reorder_level
    } for item in items]
