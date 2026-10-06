-- =====================================================================
-- WINES MANAGEMENT SYSTEM - STORED PROCEDURES
-- Database Systems Engineering Project
-- Database: wines_management_db
-- File: 06_procedures.sql
-- =====================================================================

USE wines_management_db;

DELIMITER $$

-- -------------------------------------------------------------
-- PROCEDURE 1: add_stock
-- Increases stock in inventory and wine catalog transactionally
-- -------------------------------------------------------------
DROP PROCEDURE IF EXISTS add_stock$$
CREATE PROCEDURE add_stock(
    IN p_wine_id INT,
    IN p_quantity INT
)
BEGIN
    IF p_quantity <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Stock quantity to add must be positive.';
    END IF;

    START TRANSACTION;
    
    -- Update inventory table
    UPDATE inventory 
    SET stock_quantity = stock_quantity + p_quantity
    WHERE wine_id = p_wine_id;

    -- Update wine table
    UPDATE wine
    SET quantity = quantity + p_quantity
    WHERE wine_id = p_wine_id;

    COMMIT;
    SELECT 'Stock added successfully.' AS message;
END$$

-- -------------------------------------------------------------
-- PROCEDURE 2: remove_stock
-- Decreases stock in inventory and wine catalog safely
-- -------------------------------------------------------------
DROP PROCEDURE IF EXISTS remove_stock$$
CREATE PROCEDURE remove_stock(
    IN p_wine_id INT,
    IN p_quantity INT
)
BEGIN
    DECLARE current_stock INT DEFAULT 0;

    IF p_quantity <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Quantity to remove must be positive.';
    END IF;

    SELECT stock_quantity INTO current_stock
    FROM inventory
    WHERE wine_id = p_wine_id;

    IF current_stock < p_quantity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient stock. Cannot remove more than available.';
    END IF;

    START TRANSACTION;

    UPDATE inventory
    SET stock_quantity = stock_quantity - p_quantity
    WHERE wine_id = p_wine_id;

    UPDATE wine
    SET quantity = quantity - p_quantity
    WHERE wine_id = p_wine_id;

    COMMIT;
    SELECT 'Stock removed successfully.' AS message;
END$$

-- -------------------------------------------------------------
-- PROCEDURE 3: get_customer_orders
-- Returns detailed order list for a specific customer
-- -------------------------------------------------------------
DROP PROCEDURE IF EXISTS get_customer_orders$$
CREATE PROCEDURE get_customer_orders(IN p_customer_id INT)
BEGIN
    SELECT 
        o.order_id,
        o.order_date,
        o.total_amount,
        o.payment_status,
        COUNT(od.order_detail_id) AS items_count,
        SUM(od.quantity) AS total_bottles
    FROM orders o
    LEFT JOIN order_details od ON o.order_id = od.order_id
    WHERE o.customer_id = p_customer_id
    GROUP BY o.order_id, o.order_date, o.total_amount, o.payment_status
    ORDER BY o.order_date DESC;
END$$

-- -------------------------------------------------------------
-- PROCEDURE 4: get_low_stock
-- Retrieves all items below or equal to their reorder threshold
-- -------------------------------------------------------------
DROP PROCEDURE IF EXISTS get_low_stock$$
CREATE PROCEDURE get_low_stock()
BEGIN
    SELECT 
        w.wine_id,
        w.wine_name,
        w.category,
        w.price,
        i.stock_quantity,
        i.reorder_level,
        (i.reorder_level - i.stock_quantity) AS shortage,
        s.supplier_name,
        s.phone AS supplier_phone
    FROM wine w
    JOIN inventory i ON w.wine_id = i.wine_id
    JOIN supplier s ON w.supplier_id = s.supplier_id
    WHERE i.stock_quantity <= i.reorder_level
    ORDER BY shortage DESC;
END$$

-- -------------------------------------------------------------
-- PROCEDURE 5: get_total_sales
-- Calculates aggregate revenue and order summary
-- -------------------------------------------------------------
DROP PROCEDURE IF EXISTS get_total_sales$$
CREATE PROCEDURE get_total_sales()
BEGIN
    SELECT 
        COUNT(order_id) AS total_orders,
        SUM(CASE WHEN payment_status = 'Paid' THEN total_amount ELSE 0 END) AS total_revenue_paid,
        SUM(CASE WHEN payment_status = 'Pending' THEN total_amount ELSE 0 END) AS pending_revenue,
        ROUND(AVG(total_amount), 2) AS average_order_value,
        MAX(total_amount) AS highest_order_value
    FROM orders;
END$$

DELIMITER ;

SELECT 'All 5 stored procedures created successfully!' AS status;
