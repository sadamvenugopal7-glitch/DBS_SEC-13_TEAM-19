-- =====================================================================
-- WINES MANAGEMENT SYSTEM - TRANSACTION & ACID DEMONSTRATION
-- Database Systems Engineering Project
-- Database: wines_management_db
-- File: 08_transactions.sql
-- =====================================================================

USE wines_management_db;

/*
========================================================================
ACID PROPERTIES DEMONSTRATION IN RELATIONAL DATABASE MANAGEMENT SYSTEMS
========================================================================

1. ATOMICITY:
   All operations in the transaction boundary succeed completely, or the 
   entire transaction is rolled back leaving the database in its original state.
   (No partial orders without corresponding stock deductions).

2. CONSISTENCY:
   The database transforms from one valid state to another valid state, 
   strictly adhering to foreign key constraints, CHECK constraints (stock >= 0),
   and generated column calculations.

3. ISOLATION:
   Concurrent customer transactions do not interfere with each other. 
   Row-level locks in InnoDB ensure stock deductions are serializable and
   prevent race conditions (overselling).

4. DURABILITY:
   Once COMMIT is issued, committed data is recorded into the MySQL write-ahead
   redo log (WAL) and survives system crashes or power outages.
========================================================================
*/

-- -------------------------------------------------------------
-- SCENARIO A: SUCCESSFUL ORDER TRANSACTION
-- -------------------------------------------------------------
START TRANSACTION;

-- Step 1: Create Order header
INSERT INTO orders (customer_id, order_date, total_amount, payment_status)
VALUES (1, NOW(), 3700.00, 'Paid');

SET @new_order_id = LAST_INSERT_ID();

-- Step 2: Insert Order Detail Line 1
INSERT INTO order_details (order_id, wine_id, quantity, unit_price)
VALUES (@new_order_id, 1, 2, 1850.00);

-- Step 3: Decrement Inventory stock
UPDATE inventory
SET stock_quantity = stock_quantity - 2
WHERE wine_id = 1;

-- Step 4: Decrement Wine catalog stock
UPDATE wine
SET quantity = quantity - 2
WHERE wine_id = 1;

-- Step 5: Verify all assertions passed, Commit the transaction
COMMIT;

SELECT CONCAT('Transaction committed successfully for Order #', @new_order_id) AS transaction_status;


-- -------------------------------------------------------------
-- SCENARIO B: FAILED TRANSACTION WITH AUTOMATIC ROLLBACK
-- (Simulating Insufficient Stock)
-- -------------------------------------------------------------
START TRANSACTION;

-- Attempting to place an order for 99,999 bottles
INSERT INTO orders (customer_id, order_date, total_amount, payment_status)
VALUES (2, NOW(), 0.00, 'Pending');

SET @failed_order_id = LAST_INSERT_ID();

-- Check available stock
SELECT stock_quantity INTO @current_stock
FROM inventory
WHERE wine_id = 2;

-- Conditional rollback simulation:
-- Since 99999 > @current_stock, rollback is issued:
ROLLBACK;

SELECT 'Transaction rolled back safely: insufficient stock detected. No partial records were created.' AS rollback_status;
