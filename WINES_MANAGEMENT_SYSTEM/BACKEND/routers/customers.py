"""
Wines Management System - Customers API Router
Handles customer profiles, search, safe foreign-key deletion enforcement,
CSV bulk import, and CSV data export.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from database import get_db
import crud
import schemas
from utils.csv_import import import_customers_csv
from utils.csv_export import export_customers_csv

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("", response_model=List[schemas.CustomerOut])
def read_customers(
    search: Optional[str] = Query(None, description="Search by name, phone, email, or address"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve list of customers with search and expenditure statistics."""
    return crud.get_customers(db=db, search=search, skip=skip, limit=limit)


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    """Retrieve a single customer by ID."""
    customer = crud.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return customer


@router.post("", status_code=status.HTTP_201_CREATED)
def create_customer(customer_data: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """Register a new customer."""
    created = crud.create_customer(db, customer_data)
    return {
        "success": True,
        "message": f"Customer '{created.customer_name}' added successfully.",
        "customer_id": created.customer_id
    }


@router.put("/{customer_id}")
def update_customer(customer_id: int, customer_data: schemas.CustomerUpdate, db: Session = Depends(get_db)):
    """Update customer details."""
    updated = crud.update_customer(db, customer_id, customer_data)
    return {
        "success": True,
        "message": f"Customer '{updated.customer_name}' updated successfully.",
        "customer_id": updated.customer_id
    }


@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """
    Delete customer with foreign key protection.
    If customer has orders: returns 400 with user-friendly message.
    """
    crud.delete_customer(db, customer_id)
    return {
        "success": True,
        "message": "Customer deleted successfully."
    }


@router.post("/import", response_model=schemas.CSVImportResponse)
async def upload_customers_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Batch upload customers via CSV file."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid .csv file.")
    content = await file.read()
    return import_customers_csv(db, content)


@router.get("/export/csv")
def download_customers_csv(db: Session = Depends(get_db)):
    """Download customers database as CSV file."""
    customers = crud.get_customers(db=db, limit=1000)
    return export_customers_csv(customers)
