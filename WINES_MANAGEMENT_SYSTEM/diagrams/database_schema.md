# Wines Management System - Database Schema & Design Documentation

## 1. Relational Database Overview

The **Wines Management System** is built on a normalized relational database design engineered in **MySQL 8.0**. It is structured to eliminate data redundancy, prevent update/delete anomalies, ensure referential integrity, and support high-throughput transactional queries.

---

## 2. Entity Relational Diagram (Textual Representation)

```
        ┌───────────────────────────────────┐
        │             SUPPLIER              │
        ├───────────────────────────────────┤
        │ PK  supplier_id   (INT, AUTO_INC) │
        │     supplier_name (VARCHAR 100)   │
        │     phone         (VARCHAR 20)    │
        │     email         (VARCHAR 100)   │
        │     address       (VARCHAR 255)   │
        └─────────────────┬─────────────────┘
                          │ 1
                          │ supplies
                          │ M
        ┌─────────────────▼─────────────────┐
        │               WINE                │
        ├───────────────────────────────────┤
        │ PK  wine_id       (INT, AUTO_INC) │
        │     wine_name     (VARCHAR 100)   │
        │     category      (VARCHAR 50)    │
        │     price         (DECIMAL 10,2)  │
        │     quantity      (INT)           │
        │ FK  supplier_id   (INT)           │
        └───────┬───────────────────┬───────┘
                │ 1                 │ 1
                │ contains          │ tracks
                │ M                 │ 1..M
  ┌─────────────▼────────────┐   ┌──▼────────────────────────────────┐
  │      ORDER_DETAILS       │   │            INVENTORY              │
  ├──────────────────────────┤   ├───────────────────────────────────┤
  │ PK  order_detail_id (INT)│   │ PK  inventory_id  (INT, AUTO_INC) │
  │ FK  order_id        (INT)│   │ FK  wine_id       (INT)           │
  │ FK  wine_id         (INT)│   │     stock_quantity (INT)          │
  │     quantity        (INT)│   │     reorder_level  (INT)          │
  │     unit_price   (DEC 10)│   │     last_updated  (TIMESTAMP)    │
  └─────────────▲────────────┘   └───────────────────────────────────┘
                │ M
                │ contains
                │ 1
        ┌───────┴───────────────────────────┐
        │              ORDERS               │
        ├───────────────────────────────────┤
        │ PK  order_id      (INT, AUTO_INC) │
        │ FK  customer_id   (INT)           │
        │     order_date    (DATETIME)      │
        │     total_amount  (DECIMAL 10,2)  │
        │     payment_status(VARCHAR 30)    │
        └─────────────────▲─────────────────┘
                          │ M
                          │ places
                          │ 1
        ┌─────────────────┴─────────────────┐
        │             CUSTOMER              │
        ├───────────────────────────────────┤
        │ PK  customer_id   (INT, AUTO_INC) │
        │     customer_name (VARCHAR 100)   │
        │     phone         (VARCHAR 20)    │
        │     email         (VARCHAR 100)   │
        │     address       (VARCHAR 255)   │
        └───────────────────────────────────┘
```

---

## 3. Relational Table Schemas

### 1. `supplier`
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `supplier_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for supplier |
| `supplier_name`| VARCHAR(100)| NOT NULL, CHECK (length > 0) | Name of winery / distributor |
| `phone` | VARCHAR(20) | NULL | Contact phone number |
| `email` | VARCHAR(100)| NULL | Official email address |
| `address` | VARCHAR(255)| NULL | Physical facility address |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record registration timestamp |

### 2. `wine`
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `wine_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique wine item identifier |
| `wine_name` | VARCHAR(100)| NOT NULL | Commercial label name |
| `category` | VARCHAR(50) | NOT NULL | Red, White, Rose, Sparkling, etc. |
| `price` | DECIMAL(10,2)| NOT NULL, CHECK (price > 0) | Retail price per unit |
| `quantity` | INT | DEFAULT 0, CHECK (quantity >= 0)| Current catalog stock |
| `supplier_id` | INT | FOREIGN KEY &rarr; supplier | Associated supplier ID |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

### 3. `customer`
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `customer_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique customer identifier |
| `customer_name`| VARCHAR(100)| NOT NULL, CHECK (length > 0) | Full customer name |
| `phone` | VARCHAR(20) | NULL | Customer contact telephone |
| `email` | VARCHAR(100)| NULL | Customer electronic mail |
| `address` | VARCHAR(255)| NULL | Delivery / billing address |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |

### 4. `orders`
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique sales order reference |
| `customer_id` | INT | FOREIGN KEY &rarr; customer | Buyer ID (RESTRICT delete) |
| `order_date` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Order placement timestamp |
| `total_amount` | DECIMAL(10,2)| DEFAULT 0.00, CHECK (>= 0) | Gross transaction value |
| `payment_status`| VARCHAR(30)| DEFAULT 'Pending' | Paid, Pending, Cancelled |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Order creation timestamp |

### 5. `order_details`
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `order_detail_id`| INT | PRIMARY KEY, AUTO_INCREMENT | Unique order line item ID |
| `order_id` | INT | FOREIGN KEY &rarr; orders (CASCADE) | Parent sales order ID |
| `wine_id` | INT | FOREIGN KEY &rarr; wine (RESTRICT) | Purchased wine item ID |
| `quantity` | INT | NOT NULL, CHECK (quantity > 0)| Number of bottles ordered |
| `unit_price` | DECIMAL(10,2)| NOT NULL, CHECK (>= 0) | Price locked at time of sale |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Detail record timestamp |

### 6. `inventory`
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `inventory_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique inventory tracker ID |
| `wine_id` | INT | FOREIGN KEY &rarr; wine (CASCADE) | Monitored wine item |
| `stock_quantity`| INT | DEFAULT 0, CHECK (>= 0) | Actual units physically in stock |
| `reorder_level` | INT | DEFAULT 10, CHECK (>= 0) | Low stock trigger threshold |
| `last_updated` | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP | Timestamp of last physical audit |

---

## 4. Database Normalization Analysis

The database conforms strictly to the **Third Normal Form (3NF)**:

### 1. First Normal Form (1NF) Compliance:
- **Atomic attributes**: Each column holds indivisible values. Customer names, phones, categories, and prices are single scalar values.
- **Unique row identity**: Every table possesses an unambiguous Primary Key (`*_id`).
- **No repeating groups**: Multiple ordered wines are broken down into separate rows inside `order_details` rather than stored as an array or comma-separated list inside `orders`.

### 2. Second Normal Form (2NF) Compliance:
- Satisfies 1NF.
- In tables with composite business associations (`order_details`), every non-key attribute (`quantity`, `unit_price`) depends on the entire candidate key. There are no partial functional dependencies.

### 3. Third Normal Form (3NF) Compliance:
- Satisfies 2NF.
- **No transitive dependencies**: Non-prime attributes depend only on the primary key.
  - Customer contact details (`customer_name`, `phone`, `email`) are stored exclusively in `customer`, not inside `orders`.
  - Wine information (`wine_name`, `category`, `supplier_id`) is stored exclusively in `wine`, not duplicated in `order_details`.
  - Supplier information is isolated in `supplier`.

---

## 5. ACID Transaction Implementation

When creating an order:
1. `START TRANSACTION`
2. Insert header record in `orders`
3. For each item:
   - Check available inventory stock (`stock_quantity >= quantity`)
   - Insert line record in `order_details`
   - Decrement `inventory.stock_quantity` and `wine.quantity`
4. Update `orders.total_amount`
5. If any validation fails (e.g., negative stock, missing wine), `ROLLBACK`
6. If all operations succeed, `COMMIT`
