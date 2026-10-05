"""
Wines Management System - Wines API Router
Provides RESTful endpoints for Wine catalog management, searching, sorting,
filtering, CSV batch import, and CSV data export.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from database import get_db
import crud
import schemas
from utils.csv_import import import_wines_csv
from utils.csv_export import export_wines_csv

router = APIRouter(prefix="/api/wines", tags=["Wines"])


@router.get("", response_model=List[schemas.WineOut])
def read_wines(
    search: Optional[str] = Query(None, description="Search by wine name or category"),
    category: Optional[str] = Query(None, description="Filter by category (Red Wine, White Wine, etc.)"),
    sort_by: Optional[str] = Query("wine_id", description="Sort field: price, quantity, wine_id, wine_name"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve list of wines with real backend SQL filtering and sorting."""
    return crud.get_wines(
        db=db,
        search=search,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )


@router.get("/{wine_id}")
def read_wine(wine_id: int, db: Session = Depends(get_db)):
    """Retrieve a single wine item with supplier details."""
    wine = crud.get_wine_by_id(db, wine_id)
    if not wine:
        raise HTTPException(status_code=404, detail="Wine not found.")
    return {
        "wine_id": wine.wine_id,
        "wine_name": wine.wine_name,
        "category": wine.category,
        "price": float(wine.price),
        "quantity": wine.quantity,
        "supplier_id": wine.supplier_id,
        "supplier_name": wine.supplier.supplier_name if wine.supplier else "N/A",
        "created_at": wine.created_at
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_wine(wine_data: schemas.WineCreate, db: Session = Depends(get_db)):
    """Add a new wine to the catalog with automatic inventory synchronization."""
    created = crud.create_wine(db, wine_data)
    return {
        "success": True,
        "message": f"Wine '{created.wine_name}' added successfully.",
        "wine_id": created.wine_id
    }


@router.put("/{wine_id}")
def update_wine(wine_id: int, wine_data: schemas.WineUpdate, db: Session = Depends(get_db)):
    """Update details of an existing wine."""
    updated = crud.update_wine(db, wine_id, wine_data)
    return {
        "success": True,
        "message": f"Wine '{updated.wine_name}' updated successfully.",
        "wine_id": updated.wine_id
    }


@router.delete("/{wine_id}")
def delete_wine(wine_id: int, db: Session = Depends(get_db)):
    """Delete a wine if no sales orders depend on it."""
    crud.delete_wine(db, wine_id)
    return {
        "success": True,
        "message": "Wine deleted successfully."
    }


@router.post("/import", response_model=schemas.CSVImportResponse)
async def upload_wines_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Batch upload wines via CSV file."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid .csv file.")
    content = await file.read()
    return import_wines_csv(db, content)


@router.get("/export/csv")
def download_wines_csv(db: Session = Depends(get_db)):
    """Download live wines catalog as a CSV spreadsheet."""
    wines = crud.get_wines(db=db, limit=1000)
    return export_wines_csv(wines)
