"""
Wines Management System - Suppliers API Router
Manages winery partners, distributors, contact details, CSV import and export.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from database import get_db
import crud
import schemas
from utils.csv_import import import_suppliers_csv
from utils.csv_export import export_suppliers_csv

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


@router.get("", response_model=List[schemas.SupplierOut])
def read_suppliers(
    search: Optional[str] = Query(None, description="Search by supplier name, phone, or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve list of suppliers with wine counts and search."""
    return crud.get_suppliers(db=db, search=search, skip=skip, limit=limit)


@router.get("/{supplier_id}", response_model=schemas.SupplierOut)
def read_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Retrieve supplier details by ID."""
    supplier = crud.get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return supplier


@router.post("", status_code=status.HTTP_201_CREATED)
def create_supplier(supplier_data: schemas.SupplierCreate, db: Session = Depends(get_db)):
    """Register a new supplier / winery."""
    created = crud.create_supplier(db, supplier_data)
    return {
        "success": True,
        "message": f"Supplier '{created.supplier_name}' registered successfully.",
        "supplier_id": created.supplier_id
    }


@router.put("/{supplier_id}")
def update_supplier(supplier_id: int, supplier_data: schemas.SupplierUpdate, db: Session = Depends(get_db)):
    """Update supplier information."""
    updated = crud.update_supplier(db, supplier_id, supplier_data)
    return {
        "success": True,
        "message": f"Supplier '{updated.supplier_name}' updated successfully.",
        "supplier_id": updated.supplier_id
    }


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Delete a supplier."""
    crud.delete_supplier(db, supplier_id)
    return {
        "success": True,
        "message": "Supplier deleted successfully."
    }


@router.post("/import", response_model=schemas.CSVImportResponse)
async def upload_suppliers_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Batch upload suppliers via CSV file."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid .csv file.")
    content = await file.read()
    return import_suppliers_csv(db, content)


@router.get("/export/csv")
def download_suppliers_csv(db: Session = Depends(get_db)):
    """Download suppliers database as CSV file."""
    suppliers = crud.get_suppliers(db=db, limit=1000)
    return export_suppliers_csv(suppliers)
