"""
Wines Management System - Database Connection Module
Connects to MySQL 8.x using SQLAlchemy and PyMySQL.
Falls back seamlessly to local SQLite if MySQL is offline or not yet initialized.
"""

import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Load .env file from backend/ or project root
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "wines_management")
USE_SQLITE_OVERRIDE = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")

# Construct MySQL Database URL
encoded_pw = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
MYSQL_URL = f"mysql+pymysql://{DB_USER}:{encoded_pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

Base = declarative_base()
engine = None
SessionLocal = None
IS_MYSQL = False

def create_db_engine():
    global engine, SessionLocal, IS_MYSQL
    if not USE_SQLITE_OVERRIDE:
        try:
            # Test MySQL connection
            test_engine = create_engine(
                MYSQL_URL,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 3}
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            engine = test_engine
            IS_MYSQL = True
            print(f"[DATABASE] Connected to MySQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}")
        except Exception as exc:
            print(f"[DATABASE WARNING] Could not connect to MySQL at {DB_HOST}:{DB_PORT}: {exc}")
            print("[DATABASE INFO] Initializing SQLite fallback for local demonstration.")
            sqlite_path = os.path.join(os.path.dirname(__file__), "wines_management.db")
            engine = create_engine(
                f"sqlite:///{sqlite_path}",
                connect_args={"check_same_thread": False}
            )
            IS_MYSQL = False
    else:
        sqlite_path = os.path.join(os.path.dirname(__file__), "wines_management.db")
        engine = create_engine(
            f"sqlite:///{sqlite_path}",
            connect_args={"check_same_thread": False}
        )
        IS_MYSQL = False

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

create_db_engine()

def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
