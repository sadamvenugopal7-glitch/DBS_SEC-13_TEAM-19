"""
Wines Management System - Orders API Router
Processes sales orders using robust ACID Database Transactions.
Automatically validates and decrements inventory, creates line details,
and enables multi-criteria search, filtering, and export.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
import crud
import schemas
from utils.csv_export import export_orders_csv

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("", response_model=List[schemas.OrderOut])
def read_orders(
    search: Optional[str] = Query(None, description="Search by customer name or status"),
    payment_status: Optional[str] = Query(None, description="Filter by status: Paid, Pending, Cancelled"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD start date filter"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD end date filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve list of orders with filters and summary totals."""
    return crud.get_orders(
        db=db,
        search=search,
        payment_status=payment_status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )


@router.get("/{order_id}")
def read_order(order_id: int, db: Session = Depends(get_db)):
    """Retrieve full details of an order, including customer info and itemized lines."""
    return crud.get_order_by_id(db, order_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    """
    Create Order via Database Transaction (ACID Demo):
    1. Checks customer existence.
    2. Validates available stock for each wine item.
    3. Inserts Order and OrderDetails.
    4. Automatically decrements inventory and wine catalog quantity.
    5. Calculates grand total and commits transaction; rollbacks on any failure.
    """
    return crud.create_order_transaction(db, order_in)


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Delete or cancel an order, automatically restoring inventory stock."""
    crud.delete_order(db, order_id)
    return {
        "success": True,
        "message": "Order deleted and inventory stock restored successfully."
    }


@router.get("/export/csv")
def download_orders_csv(db: Session = Depends(get_db)):
    """Download orders history as a CSV file."""
    orders = crud.get_orders(db=db, limit=1000)
    return export_orders_csv(orders)
