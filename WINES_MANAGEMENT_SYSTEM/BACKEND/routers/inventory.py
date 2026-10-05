"""
Wines Management System - Inventory API Router
Manages physical stock quantities, reorder thresholds, low-stock detection,
CSV stock uploading, and CSV stock export.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from database import get_db
import crud
import schemas
from utils.csv_import import import_inventory_csv
from utils.csv_export import export_inventory_csv

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("", response_model=List[schemas.InventoryOut])
def read_inventory(
    search: Optional[str] = Query(None, description="Search by wine name or category"),
    low_stock_only: bool = Query(False, description="Filter only records where stock <= reorder_level"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve inventory stock with status evaluation and low-stock filtering."""
    return crud.get_inventory(
        db=db,
        search=search,
        low_stock_only=low_stock_only,
        skip=skip,
        limit=limit
    )


@router.get("/low-stock", response_model=List[schemas.InventoryOut])
def read_low_stock(db: Session = Depends(get_db)):
    """Retrieve all inventory items currently at or below their reorder threshold."""
    return crud.get_inventory(db=db, low_stock_only=True, limit=500)


@router.get("/{inventory_id}", response_model=schemas.InventoryOut)
def read_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    """Retrieve a single inventory record."""
    item = crud.get_inventory_by_id(db, inventory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory record not found.")

    status_label = "LOW STOCK" if item.stock_quantity <= item.reorder_level else "AVAILABLE"
    return {
        "inventory_id": item.inventory_id,
        "wine_id": item.wine_id,
        "wine_name": item.wine.wine_name if item.wine else "Unknown",
        "category": item.wine.category if item.wine else "N/A",
        "price": float(item.wine.price) if item.wine else 0.0,
        "stock_quantity": item.stock_quantity,
        "reorder_level": item.reorder_level,
        "status": status_label,
        "last_updated": item.last_updated
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_inventory(inv_data: schemas.InventoryCreate, db: Session = Depends(get_db)):
    """Create or set inventory stock for a wine."""
    created = crud.create_inventory(db, inv_data)
    return {
        "success": True,
        "message": "Stock record created successfully.",
        "inventory_id": created.inventory_id
    }


@router.put("/{inventory_id}")
def update_inventory(inventory_id: int, inv_data: schemas.InventoryUpdate, db: Session = Depends(get_db)):
    """Update stock quantity or reorder level."""
    updated = crud.update_inventory(db, inventory_id, inv_data)
    return {
        "success": True,
        "message": "Stock updated successfully.",
        "inventory_id": updated.inventory_id
    }


@router.delete("/{inventory_id}")
def delete_inventory(inventory_id: int, db: Session = Depends(get_db)):
    """Delete an inventory record with confirmation."""
    crud.delete_inventory(db, inventory_id)
    return {
        "success": True,
        "message": "Stock record deleted successfully."
    }


@router.post("/import", response_model=schemas.CSVImportResponse)
async def upload_stock_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload Stock CSV:
    Validates wine_id, checks whether wine exists, validates stock_quantity and reorder_level,
    and returns number of successful rows and invalid rows without silently ignoring errors.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid .csv file.")
    content = await file.read()
    return import_inventory_csv(db, content)


@router.get("/export/csv")
def download_inventory_csv(db: Session = Depends(get_db)):
    """Download inventory stock as a CSV spreadsheet."""
    items = crud.get_inventory(db=db, limit=1000)
    return export_inventory_csv(items)
