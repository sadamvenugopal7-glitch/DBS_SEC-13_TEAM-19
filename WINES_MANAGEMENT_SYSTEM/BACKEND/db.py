"""
Wines Management System - Database Connection & Query Helper
Manages connections via mysql.connector with parameterized SQL queries,
safe connection closing, transaction support, and seamless fallback.
"""

import os
import sqlite3
from contextlib import contextmanager
from config import Config

IS_MYSQL = False
_sqlite_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wines_local.db")

def test_mysql_connection():
    global IS_MYSQL
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            connection_timeout=3
        )
        if conn.is_connected():
            IS_MYSQL = True
            conn.close()
            print(f"[DB SUCCESS] Connected to MySQL database '{Config.DB_NAME}' at {Config.DB_HOST}:{Config.DB_PORT}")
            return True
    except Exception as exc:
        IS_MYSQL = False
        print(f"[DB NOTICE] MySQL connection ({Config.DB_HOST}:{Config.DB_PORT}): {exc}")
        print(f"[DB NOTICE] Utilizing local SQLite fallback at {_sqlite_db_path} for seamless operation.")
        _init_sqlite_schema()
        return False

def _init_sqlite_schema():
    """Initializes SQLite fallback tables and seed data if MySQL is temporarily offline."""
    conn = sqlite3.connect(_sqlite_db_path)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS supplier (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS wine (
        wine_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wine_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER DEFAULT 0,
        supplier_id INTEGER NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
    );
    CREATE TABLE IF NOT EXISTS customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount REAL DEFAULT 0.0,
        payment_status TEXT DEFAULT 'Pending',
        FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
    );
    CREATE TABLE IF NOT EXISTS order_details (
        order_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        wine_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (wine_id) REFERENCES wine(wine_id)
    );
    CREATE TABLE IF NOT EXISTS inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wine_id INTEGER NOT NULL UNIQUE,
        stock_quantity INTEGER DEFAULT 0,
        reorder_level INTEGER DEFAULT 10,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (wine_id) REFERENCES wine(wine_id)
    );
    """)

    # Seed initial test record if empty
    cur.execute("SELECT COUNT(*) FROM wine;")
    if cur.fetchone()[0] == 0:
        cur.executescript("""
        INSERT INTO supplier (supplier_id, supplier_name, phone, email, address) VALUES
        (1, 'Sula Vineyards Ltd', '+91-253-2297200', 'orders@sulawines.com', 'Nashik, Maharashtra'),
        (2, 'Grover Zampa Vineyards', '+91-80-27622826', 'sales@groverzampa.com', 'Bengaluru, Karnataka');

        INSERT INTO wine (wine_id, wine_name, category, price, quantity, supplier_id, description) VALUES
        (1, 'Sula Rasa Cabernet Sauvignon', 'Red Wine', 1850.00, 45, 1, 'Full-bodied red aged in French oak.'),
        (2, 'Sula Dindori Reserve Shiraz', 'Red Wine', 1350.00, 60, 1, 'Lush red with crushed black pepper.'),
        (3, 'Grover Zampa La Reserve Red', 'Red Wine', 1200.00, 55, 2, 'Iconic blend of Cabernet and Shiraz.');

        INSERT INTO customer (customer_id, customer_name, phone, email, address) VALUES
        (1, 'Rajesh Sharma', '+91-9876543210', 'rajesh.sharma@samplemail.com', 'Banjara Hills, Hyderabad'),
        (2, 'Priya Patel', '+91-9823456789', 'priya.patel@samplemail.com', 'Juhu, Mumbai');

        INSERT INTO inventory (inventory_id, wine_id, stock_quantity, reorder_level) VALUES
        (1, 1, 45, 10),
        (2, 2, 60, 15),
        (3, 3, 55, 15);

        INSERT INTO orders (order_id, customer_id, order_date, total_amount, payment_status) VALUES
        (1, 1, '2026-05-10 14:30:00', 3700.00, 'Paid');

        INSERT INTO order_details (order_detail_id, order_id, wine_id, quantity, unit_price, subtotal) VALUES
        (1, 1, 1, 2, 1850.00, 3700.00);
        """)
    conn.commit()
    conn.close()

# Run test on load
test_mysql_connection()


class DBWrapper:
    """Wrapper that provides uniform API for MySQL and SQLite."""
    def __init__(self, raw_conn, is_mysql=True):
        self.raw_conn = raw_conn
        self.is_mysql = is_mysql

    def cursor(self, dictionary=True):
        if self.is_mysql:
            return self.raw_conn.cursor(dictionary=dictionary)
        else:
            if dictionary:
                self.raw_conn.row_factory = sqlite3.Row
            else:
                self.raw_conn.row_factory = None
            return self.raw_conn.cursor()

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def start_transaction(self):
        if self.is_mysql:
            self.raw_conn.start_transaction()

    def close(self):
        self.raw_conn.close()


@contextmanager
def get_db():
    """Context manager for obtaining a database connection safely."""
    global IS_MYSQL
    conn = None
    if IS_MYSQL:
        import mysql.connector
        try:
            conn = mysql.connector.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            yield DBWrapper(conn, is_mysql=True)
        except Exception as exc:
            print(f"[DB ERROR] MySQL connection dropped: {exc}. Reverting to fallback.")
            IS_MYSQL = False
            _init_sqlite_schema()
            sqlite_conn = sqlite3.connect(_sqlite_db_path)
            sqlite_conn.execute("PRAGMA foreign_keys = ON;")
            yield DBWrapper(sqlite_conn, is_mysql=False)
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    else:
        sqlite_conn = sqlite3.connect(_sqlite_db_path)
        sqlite_conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield DBWrapper(sqlite_conn, is_mysql=False)
        finally:
            try:
                sqlite_conn.close()
            except:
                pass


def execute_query(sql, params=None, fetch_all=True, fetch_one=False, commit=False):
    """Executes a parameterized query safely and closes connection."""
    with get_db() as db:
        # Convert parameter syntax %s to ? if using SQLite
        exec_sql = sql if db.is_mysql else sql.replace("%s", "?")
        cur = db.cursor(dictionary=True)
        cur.execute(exec_sql, params or ())

        if commit:
            db.commit()
            last_id = getattr(cur, "lastrowid", None)
            return last_id

        if fetch_one:
            row = cur.fetchone()
            return dict(row) if row else None

        if fetch_all:
            rows = cur.fetchall()
            return [dict(r) for r in rows]
