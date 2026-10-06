-- =====================================================================
-- WINES MANAGEMENT SYSTEM - MYSQL DATA EXPORT COMMANDS
-- Database: wines_management_db
-- File: 09_export.sql
-- =====================================================================

USE wines_management_db;

-- -------------------------------------------------------------
-- 1. MYSQLDUMP COMMAND (Run in Windows Command Prompt / PowerShell)
-- -------------------------------------------------------------
-- Complete database backup command:
-- mysqldump -u root -p --routines --triggers --events wines_management_db > complete_database_backup.sql

-- -------------------------------------------------------------
-- 2. CSV EXPORT QUERIES FOR MYSQL WORKBENCH
-- Execute each query in Workbench and click 'Export Recordset to an External File' (CSV)
-- -------------------------------------------------------------

-- Export Suppliers
SELECT supplier_id, supplier_name, phone, email, address, created_at
FROM supplier
ORDER BY supplier_id;

-- Export Wines
SELECT wine_id, wine_name, category, price, quantity, supplier_id, description, created_at
FROM wine
ORDER BY wine_id;

-- Export Customers (250 Records)
SELECT customer_id, customer_name, phone, email, address, created_at
FROM customer
ORDER BY customer_id;

-- Export Inventory
SELECT inventory_id, wine_id, stock_quantity, reorder_level, last_updated
FROM inventory
ORDER BY inventory_id;

-- Export Orders
SELECT order_id, customer_id, order_date, total_amount, payment_status
FROM orders
ORDER BY order_id;

-- Export Order Details
SELECT order_detail_id, order_id, wine_id, quantity, unit_price, subtotal
FROM order_details
ORDER BY order_detail_id;
