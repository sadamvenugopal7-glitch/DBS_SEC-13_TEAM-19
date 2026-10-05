"""
Wines Management System - Database Export API Router
Streams complete SQL schemas, sample datasets, and full database dumps for MySQL Workbench.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

router = APIRouter(prefix="/api/export", tags=["Database Export"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(os.path.dirname(BASE_DIR), "database")


def get_sql_file_response(filename: str, download_name: str) -> FileResponse:
    file_path = os.path.join(DATABASE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"SQL export file '{filename}' not found.")
    return FileResponse(
        path=file_path,
        media_type="application/sql",
        filename=download_name
    )


@router.get("/schema")
def download_schema():
    """Download database_schema.sql (DDL with tables, constraints, indexes)."""
    return get_sql_file_response("02_create_tables.sql", "database_schema.sql")


@router.get("/sample-data")
def download_sample_data():
    """Download sample_data.sql (DML with realistic seed data)."""
    return get_sql_file_response("03_insert_sample_data.sql", "sample_data.sql")


@router.get("/complete")
def download_complete_database():
    """Download complete_database.sql (Consolidated DDL, DML, Views, Procedures, Triggers)."""
    return get_sql_file_response("08_export_database.sql", "complete_database.sql")


@router.get("/queries")
def download_queries():
    """Download 04_queries.sql for academic DBMS query demonstration."""
    return get_sql_file_response("04_queries.sql", "queries_demonstration.sql")


@router.get("/views")
def download_views():
    """Download 05_views.sql."""
    return get_sql_file_response("05_views.sql", "database_views.sql")


@router.get("/procedures")
def download_procedures():
    """Download 06_procedures.sql."""
    return get_sql_file_response("06_procedures.sql", "stored_procedures.sql")


@router.get("/triggers")
def download_triggers():
    """Download 07_triggers.sql."""
    return get_sql_file_response("07_triggers.sql", "database_triggers.sql")
