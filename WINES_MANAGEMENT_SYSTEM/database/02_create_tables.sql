-- =====================================================================
-- WINES MANAGEMENT SYSTEM
-- Database Tables DDL & Constraints
-- Database: wines_management_db
-- File: 02_create_tables.sql
-- =====================================================================

USE wines_management_db;

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS order_details;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS wine;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS supplier;

-- -------------------------------------------------------------
-- TABLE 1: SUPPLIER
-- -------------------------------------------------------------
CREATE TABLE supplier (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------
-- TABLE 2: WINE
-- -------------------------------------------------------------
CREATE TABLE wine (
    wine_id INT PRIMARY KEY AUTO_INCREMENT,
    wine_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    quantity INT DEFAULT 0,
    supplier_id INT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_wine_price CHECK (price >= 0),
    CONSTRAINT chk_wine_quantity CHECK (quantity >= 0),
    CONSTRAINT fk_wine_supplier FOREIGN KEY (supplier_id)
        REFERENCES supplier(supplier_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------
-- TABLE 3: CUSTOMER
-- -------------------------------------------------------------
CREATE TABLE customer (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------
-- TABLE 4: ORDERS
-- -------------------------------------------------------------
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12, 2) DEFAULT 0.00,
    payment_status VARCHAR(30) DEFAULT 'Pending',
    CONSTRAINT chk_order_total CHECK (total_amount >= 0),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------
-- TABLE 5: ORDER_DETAILS
-- -------------------------------------------------------------
CREATE TABLE order_details (
    order_detail_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    wine_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    CONSTRAINT chk_detail_quantity CHECK (quantity > 0),
    CONSTRAINT chk_detail_unit_price CHECK (unit_price >= 0),
    CONSTRAINT fk_details_order FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_details_wine FOREIGN KEY (wine_id)
        REFERENCES wine(wine_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------
-- TABLE 6: INVENTORY
-- -------------------------------------------------------------
CREATE TABLE inventory (
    inventory_id INT PRIMARY KEY AUTO_INCREMENT,
    wine_id INT NOT NULL UNIQUE,
    stock_quantity INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_inv_stock CHECK (stock_quantity >= 0),
    CONSTRAINT chk_inv_reorder CHECK (reorder_level >= 0),
    CONSTRAINT fk_inventory_wine FOREIGN KEY (wine_id)
        REFERENCES wine(wine_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------
-- PERFORMANCE INDEXES (Section 54)
-- -------------------------------------------------------------
CREATE INDEX idx_customer_email ON customer(email);
CREATE INDEX idx_customer_phone ON customer(phone);
CREATE INDEX idx_wine_name ON wine(wine_name);
CREATE INDEX idx_wine_category ON wine(category);
CREATE INDEX idx_wine_supplier ON wine(supplier_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_details_order ON order_details(order_id);
CREATE INDEX idx_order_details_wine ON order_details(wine_id);
CREATE INDEX idx_inventory_wine ON inventory(wine_id);

SELECT 'All 6 tables and performance indexes created successfully!' AS status;
