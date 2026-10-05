"""
Wines Management System - FastAPI Application Entry Point
Mounts REST API routers, static frontend files, CORS middleware,
and provides automatic table creation and seed data verification on startup.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from database import engine, Base, SessionLocal, IS_MYSQL
import models
from routers import wines, suppliers, customers, inventory, orders, dashboard, export


# Base Directories
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")


def seed_initial_data_if_empty():
    """Checks if database is populated. If empty, seeds initial data automatically."""
    db = SessionLocal()
    try:
        wine_count = db.query(models.Wine).count()
        if wine_count == 0:
            print("[STARTUP] Database is empty. Loading initial sample data...")
            sample_sql_path = os.path.join(DATABASE_DIR, "03_insert_sample_data.sql")
            if os.path.exists(sample_sql_path):
                with open(sample_sql_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Execute statement by statement
                statements = [stmt.strip() for stmt in content.split(";") if stmt.strip() and not stmt.strip().startswith("--")]
                for stmt in statements:
                    if stmt.upper().startswith("USE ") or stmt.upper().startswith("SELECT "):
                        continue
                    try:
                        from sqlalchemy import text
                        db.execute(text(stmt))
                    except Exception as e:
                        # Silently continue on duplicate statements
                        pass
                db.commit()
                print("[STARTUP] Sample dataset seeded successfully!")
    except Exception as exc:
        db.rollback()
        print(f"[STARTUP NOTE] Seed check info: {exc}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup if not already created
    try:
        Base.metadata.create_all(bind=engine)
        seed_initial_data_if_empty()
    except Exception as e:
        print(f"[STARTUP WARNING] Table creation note: {e}")
    yield


app = FastAPI(
    title="Wines Management System API",
    description="Relational DBMS & Full-Stack Backend for Wines, Suppliers, Customers, Inventory, and Sales Orders.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(wines.router)
app.include_router(suppliers.router)
app.include_router(customers.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
app.include_router(dashboard.reports_router)
app.include_router(export.router)


# Global Exception Handler for friendly error messages
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "A database or system error occurred.",
            "detail": str(exc)
        }
    )


# Mount Frontend Static Assets
if os.path.exists(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")


# Frontend HTML Page Routes
@app.get("/", include_in_schema=False)
def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/wines.html", include_in_schema=False)
def serve_wines_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "wines.html"))

@app.get("/customers.html", include_in_schema=False)
def serve_customers_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "customers.html"))

@app.get("/suppliers.html", include_in_schema=False)
def serve_suppliers_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "suppliers.html"))

@app.get("/inventory.html", include_in_schema=False)
def serve_inventory_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "inventory.html"))

@app.get("/orders.html", include_in_schema=False)
def serve_orders_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "orders.html"))

@app.get("/reports.html", include_in_schema=False)
def serve_reports_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "reports.html"))

@app.get("/export.html", include_in_schema=False)
def serve_export_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "export.html"))

@app.get("/erd.html", include_in_schema=False)
def serve_erd_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "erd.html"))


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "Wines Management System",
        "database_engine": "MySQL" if IS_MYSQL else "SQLite (Fallback)",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
