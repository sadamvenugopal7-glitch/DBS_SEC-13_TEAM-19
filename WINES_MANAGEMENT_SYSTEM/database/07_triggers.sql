-- =====================================================================
-- WINES MANAGEMENT SYSTEM - DATABASE TRIGGERS
-- Database Systems Engineering Project
-- Database: wines_management_db
-- File: 07_triggers.sql
-- =====================================================================

USE wines_management_db;

DELIMITER $$

-- -------------------------------------------------------------
-- TRIGGER 1: Check Stock Availability & Prevent Negative Stock
-- Fires BEFORE INSERT on order_details
-- -------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_prevent_negative_inventory$$
CREATE TRIGGER trg_prevent_negative_inventory
BEFORE INSERT ON order_details
FOR EACH ROW
BEGIN
    DECLARE available_stock INT DEFAULT 0;

    SELECT stock_quantity INTO available_stock
    FROM inventory
    WHERE wine_id = NEW.wine_id
    LIMIT 1;

    IF available_stock IS NULL OR available_stock < NEW.quantity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient stock. Operation aborted by database integrity trigger.';
    END IF;
END$$

-- -------------------------------------------------------------
-- TRIGGER 2: Auto-Update Order Total Amount
-- Fires AFTER INSERT on order_details
-- -------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_update_order_total_insert$$
CREATE TRIGGER trg_update_order_total_insert
AFTER INSERT ON order_details
FOR EACH ROW
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT COALESCE(SUM(subtotal), 0)
        FROM order_details
        WHERE order_id = NEW.order_id
    )
    WHERE order_id = NEW.order_id;
END$$

-- -------------------------------------------------------------
-- TRIGGER 3: Auto-Update Order Total on Item Deletion
-- Fires AFTER DELETE on order_details
-- -------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_update_order_total_delete$$
CREATE TRIGGER trg_update_order_total_delete
AFTER DELETE ON order_details
FOR EACH ROW
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT COALESCE(SUM(subtotal), 0)
        FROM order_details
        WHERE order_id = OLD.order_id
    )
    WHERE order_id = OLD.order_id;
END$$

DELIMITER ;

SELECT 'All triggers created successfully!' AS status;
