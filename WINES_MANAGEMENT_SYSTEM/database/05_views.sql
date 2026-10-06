-- =====================================================================
-- WINES MANAGEMENT SYSTEM - SQL VIEWS
-- Database Systems Engineering Project
-- Database: wines_management_db
-- File: 05_views.sql
-- =====================================================================

USE wines_management_db;

-- -------------------------------------------------------------
-- VIEW 1: available_stock_view
-- -------------------------------------------------------------
DROP VIEW IF EXISTS available_stock_view;
CREATE VIEW available_stock_view AS
SELECT 
    w.wine_id,
    w.wine_name,
    w.category,
    w.price,
    i.stock_quantity,
    i.reorder_level,
    (i.stock_quantity - i.reorder_level) AS safety_stock,
    'IN STOCK' AS stock_status,
    s.supplier_name
FROM wine w
JOIN inventory i ON w.wine_id = i.wine_id
JOIN supplier s ON w.supplier_id = s.supplier_id
WHERE i.stock_quantity > i.reorder_level;

-- -------------------------------------------------------------
-- VIEW 2: low_stock_view
-- -------------------------------------------------------------
DROP VIEW IF EXISTS low_stock_view;
CREATE VIEW low_stock_view AS
SELECT 
    w.wine_id,
    w.wine_name,
    w.category,
    w.price,
    i.stock_quantity,
    i.reorder_level,
    CASE 
        WHEN i.stock_quantity = 0 THEN 'OUT OF STOCK'
        ELSE 'LOW STOCK'
    END AS stock_status,
    s.supplier_name,
    s.phone AS supplier_phone,
    s.email AS supplier_email
FROM wine w
JOIN inventory i ON w.wine_id = i.wine_id
JOIN supplier s ON w.supplier_id = s.supplier_id
WHERE i.stock_quantity <= i.reorder_level;

-- -------------------------------------------------------------
-- VIEW 3: customer_order_history_view
-- -------------------------------------------------------------
DROP VIEW IF EXISTS customer_order_history_view;
CREATE VIEW customer_order_history_view AS
SELECT 
    c.customer_id,
    c.customer_name,
    c.phone,
    c.email,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0.00) AS total_spent,
    MAX(o.order_date) AS latest_order_date
FROM customer c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.phone, c.email;

-- -------------------------------------------------------------
-- VIEW 4: sales_summary_view
-- -------------------------------------------------------------
DROP VIEW IF EXISTS sales_summary_view;
CREATE VIEW sales_summary_view AS
SELECT 
    w.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(od.quantity) AS total_bottles_sold,
    SUM(od.subtotal) AS gross_revenue,
    ROUND(AVG(od.unit_price), 2) AS average_selling_price
FROM order_details od
JOIN wine w ON od.wine_id = w.wine_id
JOIN orders o ON od.order_id = o.order_id
WHERE o.payment_status = 'Paid'
GROUP BY w.category;

-- -------------------------------------------------------------
-- VIEW 5: wine_sales_view
-- -------------------------------------------------------------
DROP VIEW IF EXISTS wine_sales_view;
CREATE VIEW wine_sales_view AS
SELECT 
    w.wine_id,
    w.wine_name,
    w.category,
    w.price AS catalog_price,
    COALESCE(SUM(od.quantity), 0) AS total_units_sold,
    COALESCE(SUM(od.subtotal), 0.00) AS total_revenue
FROM wine w
LEFT JOIN order_details od ON w.wine_id = od.wine_id
GROUP BY w.wine_id, w.wine_name, w.category, w.price;

SELECT 'All 5 SQL views created successfully!' AS status;
