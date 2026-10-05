"""
Wines Management System - Database Initializer & Setup Script
Run this script to initialize the MySQL database and load all tables, views,
procedures, triggers, and sample data.
Usage: python init_db.py
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "wines_management")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")

SQL_FILES = [
    "01_create_database.sql",
    "02_create_tables.sql",
    "03_insert_sample_data.sql",
    "04_queries.sql",
    "05_views.sql",
    "06_procedures.sql",
    "07_triggers.sql"
]


def run_init():
    print("=" * 65)
    print("WINES MANAGEMENT SYSTEM - MYSQL DATABASE INITIALIZATION")
    print("=" * 65)
    print(f"Target Server: {DB_HOST}:{DB_PORT}")
    print(f"User:          {DB_USER}")
    print(f"Database:      {DB_NAME}")
    print("-" * 65)

    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True,
            client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
        )
        print("[SUCCESS] Connected to MySQL Server!")
    except Exception as exc:
        print(f"[ERROR] Could not connect to MySQL server: {exc}")
        print("\nPlease check:")
        print("1. MySQL service (MySQL80) is running.")
        print("2. The DB_PASSWORD in your .env file is correct.")
        sys.exit(1)

    cursor = conn.cursor()

    for sql_file in SQL_FILES:
        file_path = os.path.join(DATABASE_DIR, sql_file)
        if not os.path.exists(file_path):
            print(f"[SKIP] File not found: {sql_file}")
            continue

        print(f"\n[EXECUTING] {sql_file}...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Execute statements
            cursor.execute(content)
            print(f"[OK] {sql_file} executed successfully.")
        except Exception as err:
            print(f"[WARNING] Note while running {sql_file}: {err}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 65)
    print("[COMPLETED] Wines Management System Database setup successfully!")
    print("=" * 65)


if __name__ == "__main__":
    run_init()
