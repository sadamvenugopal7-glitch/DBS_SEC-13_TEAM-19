-- =====================================================================
-- WINES MANAGEMENT SYSTEM - REQUIRED SQL QUERIES
-- Academic DBMS Demonstration
-- Database: wines_management_db
-- File: 04_queries.sql
-- =====================================================================

USE wines_management_db;

-- -------------------------------------------------------------
-- 1. BASIC SELECT STATEMENTS
-- -------------------------------------------------------------
-- SELECT all wines
SELECT * FROM wine;

-- SELECT all customers
SELECT * FROM customer;

-- SELECT all suppliers
SELECT * FROM supplier;

-- SELECT all inventory records
SELECT * FROM inventory;

-- -------------------------------------------------------------
-- 2. INNER JOIN: Wine and Supplier Information
-- -------------------------------------------------------------
SELECT 
    w.wine_name,
    w.category,
    w.price,
    s.supplier_name
FROM wine w
JOIN supplier s ON w.supplier_id = s.supplier_id;

-- -------------------------------------------------------------
-- 3. JOIN: Customer Order History
-- -------------------------------------------------------------
SELECT 
    c.customer_name,
    o.order_id,
    o.order_date,
    o.total_amount,
    o.payment_status
FROM customer c
JOIN orders o ON c.customer_id = o.customer_id;

-- -------------------------------------------------------------
-- 4. MULTI-TABLE JOIN: Order Details with Customer and Wine
-- -------------------------------------------------------------
SELECT 
    o.order_id,
    c.customer_name,
    w.wine_name,
    od.quantity,
    od.unit_price,
    od.subtotal
FROM orders o
JOIN customer c ON o.customer_id = c.customer_id
JOIN order_details od ON o.order_id = od.order_id
JOIN wine w ON od.wine_id = w.wine_id;

-- -------------------------------------------------------------
-- 5. FILTER / WHERE: Low-Stock Inventory Items
-- -------------------------------------------------------------
SELECT 
    w.wine_name,
    i.stock_quantity,
    i.reorder_level
FROM wine w
JOIN inventory i ON w.wine_id = i.wine_id
WHERE i.stock_quantity <= i.reorder_level;

-- -------------------------------------------------------------
-- 6. AGGREGATE FUNCTION: SUM Total Sales (Paid Orders)
-- -------------------------------------------------------------
SELECT SUM(total_amount) AS total_sales
FROM orders
WHERE payment_status = 'Paid';

-- -------------------------------------------------------------
-- 7. AGGREGATE FUNCTION: COUNT Customers
-- -------------------------------------------------------------
SELECT COUNT(*) AS total_customers
FROM customer;

-- -------------------------------------------------------------
-- 8. AGGREGATE FUNCTION: AVG Wine Price
-- -------------------------------------------------------------
SELECT ROUND(AVG(price), 2) AS average_price
FROM wine;

-- -------------------------------------------------------------
-- 9. GROUP BY & COUNT: Category Grouping
-- -------------------------------------------------------------
SELECT 
    category,
    COUNT(*) AS wine_count
FROM wine
GROUP BY category;

-- -------------------------------------------------------------
-- 10. GROUP BY & ORDER BY: Top Selling Wines by Quantity Sold
-- -------------------------------------------------------------
SELECT 
    w.wine_name,
    SUM(od.quantity) AS total_quantity
FROM order_details od
JOIN wine w ON od.wine_id = w.wine_id
GROUP BY w.wine_id, w.wine_name
ORDER BY total_quantity DESC;

-- -------------------------------------------------------------
-- 11. ADVANCED: Sales Volume and Revenue by Category
-- -------------------------------------------------------------
SELECT 
    w.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(od.quantity) AS total_bottles_sold,
    SUM(od.subtotal) AS gross_revenue
FROM order_details od
JOIN wine w ON od.wine_id = w.wine_id
JOIN orders o ON od.order_id = o.order_id
GROUP BY w.category
ORDER BY gross_revenue DESC;

-- -------------------------------------------------------------
-- 12. ADVANCED: Customers with High Order Totals (HAVING)
-- -------------------------------------------------------------
SELECT 
    c.customer_name,
    c.email,
    COUNT(o.order_id) AS orders_count,
    SUM(o.total_amount) AS total_spent
FROM customer c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.payment_status = 'Paid'
GROUP BY c.customer_id, c.customer_name, c.email
HAVING SUM(o.total_amount) > 5000.00
ORDER BY total_spent DESC;
