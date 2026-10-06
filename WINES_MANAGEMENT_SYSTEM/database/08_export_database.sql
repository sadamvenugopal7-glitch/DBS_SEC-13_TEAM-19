-- =====================================================================
-- WINES MANAGEMENT SYSTEM - COMPLETE CONSOLIDATED DATABASE EXPORT
-- Academic DBMS Project
-- Ready to run directly in MySQL Workbench, MySQL CLI, or phpMyAdmin
-- File: 08_export_database.sql
-- =====================================================================

DROP DATABASE IF EXISTS wines_management;
CREATE DATABASE wines_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE wines_management;

-- -------------------------------------------------------------
-- 1. DDL: TABLE CREATION
-- -------------------------------------------------------------

DROP TABLE IF EXISTS order_details;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS wine;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS supplier;

CREATE TABLE supplier (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_supplier_name CHECK (CHAR_LENGTH(TRIM(supplier_name)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE wine (
    wine_id INT PRIMARY KEY AUTO_INCREMENT,
    wine_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    quantity INT DEFAULT 0,
    supplier_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_wine_price CHECK (price > 0),
    CONSTRAINT chk_wine_quantity CHECK (quantity >= 0),
    CONSTRAINT fk_wine_supplier FOREIGN KEY (supplier_id) 
        REFERENCES supplier(supplier_id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE customer (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_customer_name CHECK (CHAR_LENGTH(TRIM(customer_name)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) DEFAULT 0.00,
    payment_status VARCHAR(30) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_order_total CHECK (total_amount >= 0),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(customer_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE order_details (
    order_detail_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    wine_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_detail_quantity CHECK (quantity > 0),
    CONSTRAINT chk_detail_unit_price CHECK (unit_price >= 0),
    CONSTRAINT fk_details_order FOREIGN KEY (order_id) 
        REFERENCES orders(order_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_details_wine FOREIGN KEY (wine_id) 
        REFERENCES wine(wine_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE inventory (
    inventory_id INT PRIMARY KEY AUTO_INCREMENT,
    wine_id INT NOT NULL,
    stock_quantity INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_inventory_stock CHECK (stock_quantity >= 0),
    CONSTRAINT chk_inventory_reorder CHECK (reorder_level >= 0),
    CONSTRAINT fk_inventory_wine FOREIGN KEY (wine_id) 
        REFERENCES wine(wine_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- INDEXES
CREATE INDEX idx_wine_category ON wine(category);
CREATE INDEX idx_wine_price ON wine(price);
CREATE INDEX idx_wine_supplier ON wine(supplier_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_details_order ON order_details(order_id);
CREATE INDEX idx_order_details_wine ON order_details(wine_id);
CREATE INDEX idx_inventory_wine ON inventory(wine_id);
CREATE INDEX idx_inventory_stock ON inventory(stock_quantity);

-- -------------------------------------------------------------
-- 2. DDL: VIEWS
-- -------------------------------------------------------------

CREATE VIEW view_available_stock AS
SELECT 
    i.inventory_id,
    w.wine_id,
    w.wine_name,
    w.category,
    w.price,
    i.stock_quantity,
    i.reorder_level,
    (i.stock_quantity - i.reorder_level) AS safety_margin,
    'AVAILABLE' AS stock_status,
    i.last_updated
FROM inventory i
JOIN wine w ON i.wine_id = w.wine_id
WHERE i.stock_quantity > i.reorder_level;

CREATE VIEW view_low_stock AS
SELECT 
    i.inventory_id,
    w.wine_id,
    w.wine_name,
    w.category,
    w.price,
    i.stock_quantity,
    i.reorder_level,
    (i.reorder_level - i.stock_quantity) AS deficit,
    'LOW STOCK' AS stock_status,
    s.supplier_name,
    s.phone AS supplier_phone,
    s.email AS supplier_email,
    i.last_updated
FROM inventory i
JOIN wine w ON i.wine_id = w.wine_id
LEFT JOIN supplier s ON w.supplier_id = s.supplier_id
WHERE i.stock_quantity <= i.reorder_level;

CREATE VIEW view_customer_orders AS
SELECT 
    c.customer_id,
    c.customer_name,
    c.phone,
    c.email,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0.00) AS total_revenue,
    MAX(o.order_date) AS last_order_date
FROM customer c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.phone, c.email;

CREATE VIEW view_total_sales AS
SELECT 
    w.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(od.quantity) AS total_bottles_sold,
    SUM(od.quantity * od.unit_price) AS total_category_revenue,
    ROUND(AVG(od.unit_price), 2) AS average_selling_price
FROM order_details od
JOIN wine w ON od.wine_id = w.wine_id
JOIN orders o ON od.order_id = o.order_id
GROUP BY w.category;

CREATE VIEW view_wine_supplier AS
SELECT 
    w.wine_id,
    w.wine_name,
    w.category,
    w.price,
    w.quantity AS current_wine_quantity,
    s.supplier_id,
    s.supplier_name,
    s.phone AS supplier_phone,
    s.email AS supplier_email,
    s.address AS supplier_address
FROM wine w
LEFT JOIN supplier s ON w.supplier_id = s.supplier_id;

-- -------------------------------------------------------------
-- 3. DDL: PROCEDURES & TRIGGERS
-- -------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE get_customer_orders(IN p_customer_id INT)
BEGIN
    SELECT o.order_id, o.order_date, o.payment_status, o.total_amount, COUNT(od.order_detail_id) AS total_items, SUM(od.quantity) AS total_bottles
    FROM orders o LEFT JOIN order_details od ON o.order_id = od.order_id
    WHERE o.customer_id = p_customer_id GROUP BY o.order_id, o.order_date, o.payment_status, o.total_amount ORDER BY o.order_date DESC;
END$$

CREATE PROCEDURE get_low_stock()
BEGIN
    SELECT i.inventory_id, w.wine_id, w.wine_name, w.category, w.price, i.stock_quantity, i.reorder_level, (i.reorder_level - i.stock_quantity) AS units_needed, s.supplier_name, s.phone AS supplier_phone, s.email AS supplier_email
    FROM inventory i JOIN wine w ON i.wine_id = w.wine_id LEFT JOIN supplier s ON w.supplier_id = s.supplier_id
    WHERE i.stock_quantity <= i.reorder_level ORDER BY (i.reorder_level - i.stock_quantity) DESC;
END$$

CREATE PROCEDURE get_total_sales()
BEGIN
    SELECT COUNT(order_id) AS total_orders, SUM(CASE WHEN payment_status = 'Paid' THEN total_amount ELSE 0 END) AS total_revenue_paid, SUM(CASE WHEN payment_status = 'Pending' THEN total_amount ELSE 0 END) AS pending_revenue, ROUND(AVG(total_amount), 2) AS average_order_value, MAX(total_amount) AS highest_order_value FROM orders;
END$$

CREATE PROCEDURE search_wines(IN p_search_text VARCHAR(100))
BEGIN
    SET @pattern = CONCAT('%', TRIM(p_search_text), '%');
    SELECT w.wine_id, w.wine_name, w.category, w.price, w.quantity AS catalog_quantity, COALESCE(i.stock_quantity, 0) AS inventory_stock, COALESCE(i.reorder_level, 10) AS reorder_level, s.supplier_name
    FROM wine w LEFT JOIN inventory i ON w.wine_id = i.wine_id LEFT JOIN supplier s ON w.supplier_id = s.supplier_id
    WHERE w.wine_name LIKE @pattern OR w.category LIKE @pattern OR s.supplier_name LIKE @pattern
    ORDER BY w.wine_name ASC;
END$$

CREATE TRIGGER trg_before_order_details_insert
BEFORE INSERT ON order_details
FOR EACH ROW
BEGIN
    DECLARE available_stock INT DEFAULT 0;
    SELECT stock_quantity INTO available_stock FROM inventory WHERE wine_id = NEW.wine_id LIMIT 1;
    IF available_stock IS NULL OR available_stock < NEW.quantity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock for the requested wine in inventory.';
    END IF;
END$$

CREATE TRIGGER trg_after_order_details_insert
AFTER INSERT ON order_details
FOR EACH ROW
BEGIN
    UPDATE inventory SET stock_quantity = stock_quantity - NEW.quantity WHERE wine_id = NEW.wine_id;
    UPDATE wine SET quantity = GREATEST(0, quantity - NEW.quantity) WHERE wine_id = NEW.wine_id;
END$$

CREATE TRIGGER trg_after_order_details_delete
AFTER DELETE ON order_details
FOR EACH ROW
BEGIN
    UPDATE inventory SET stock_quantity = stock_quantity + OLD.quantity WHERE wine_id = OLD.wine_id;
    UPDATE wine SET quantity = quantity + OLD.quantity WHERE wine_id = OLD.wine_id;
END$$

DELIMITER ;

-- -------------------------------------------------------------
-- 4. DML: SAMPLE DATA INSERTION
-- -------------------------------------------------------------
INSERT INTO supplier (supplier_id, supplier_name, phone, email, address) VALUES
(1, 'Sula Vineyards Ltd', '+91-253-2297200', 'orders@sulawines.com', 'Govardhan Village, Gangapur Dam Road, Nashik, Maharashtra'),
(2, 'Grover Zampa Vineyards', '+91-80-27622826', 'sales@groverzampa.com', 'Raghunathapur, Doddaballapur Road, Bengaluru, Karnataka'),
(3, 'Fratelli Wines Pvt Ltd', '+91-218-4228000', 'contact@fratelliwines.in', 'Akluj, Solapur District, Maharashtra'),
(4, 'York Winery & Tasting Room', '+91-253-2230700', 'info@yorkwinery.com', 'Gangavarhe Village, Gangapur Dam, Nashik, Maharashtra'),
(5, 'KRSMA Estates Vineyard', '+91-83-94240500', 'cellar@krsmaestates.com', 'Hampi Hills, Koppal District, Karnataka'),
(6, 'Vallonne Vineyards Boutique', '+91-9769138346', 'enquiry@vallonnevineyards.com', 'Kavnai, Igatpuri, Nashik, Maharashtra'),
(7, 'Soma Vine Village', '+91-7028065001', 'reservations@somavinevillage.com', 'Village Ganghavare, Gangapur-Savargaon Road, Nashik'),
(8, 'Domaine Chandon India', '+91-253-3049100', 'chandonservice@chandon.co.in', 'Dindori, Nashik District, Maharashtra'),
(9, 'Charosa Wineries Ltd', '+91-22-67097777', 'orders@charosawineries.com', 'Charosa Village, Dindori Taluka, Nashik, Maharashtra'),
(10, 'Vintage Wines (Reveilo)', '+91-255-6258010', 'reveilo@vintagewines.co.in', 'Niphad, Nashik District, Maharashtra'),
(11, 'Four Seasons Vineyards', '+91-211-2244200', 'cellar@fourseasonsvineyards.com', 'Rangaon, Daund Taluka, Pune District, Maharashtra'),
(12, 'Good Earth Winery Co', '+91-253-2341200', 'sales@goodearthwinery.com', 'Vinchur Wine Park, Nashik, Maharashtra'),
(13, 'Big Banyan Wines Ltd', '+91-80-41235678', 'contact@bigbanyanwines.com', 'Kalyanipura, Nelamangala Taluk, Bengaluru Rural'),
(14, 'Chateau Indage Heritage', '+91-211-4237100', 'heritage@chateauindage.com', 'Narayangaon, Pune District, Maharashtra'),
(15, 'Renaissance Winery Nashik', '+91-253-2415500', 'sales@renaissancewinery.net', 'Ozar, Nashik-Agra Highway, Maharashtra'),
(16, 'Mokssh Vineyards India', '+91-253-6691234', 'info@moksshwines.com', 'Dindori Valley, Nashik, Maharashtra'),
(17, 'Deccan Plateau Cellars', '+91-83-22741200', 'info@deccanplateau.in', 'Bilekallu Village, Bijapur District, Karnataka'),
(18, 'Aarna Wine Distributors', '+91-40-23351299', 'aarnawines@distributors.com', 'Banjara Hills Road No 12, Hyderabad, Telangana'),
(19, 'Nashik Valley Estates', '+91-253-2570088', 'sales@nashikvalley.com', 'MIDC Ambad, Nashik, Maharashtra'),
(20, 'Heritage Grape Winery', '+91-80-22214455', 'heritage@grapewinery.in', 'Kengeri Satellite Town, Bengaluru, Karnataka'),
(21, 'Tuscan Heritage Importers', '+91-22-40019900', 'import@tuscanheritage.com', 'Worli Seaface, Mumbai, Maharashtra'),
(22, 'Bordeaux Selections India', '+91-11-41527788', 'contact@bordeauxselections.in', 'Connaught Place, New Delhi'),
(23, 'Goa Portuguese Cellars', '+91-832-2431200', 'portuguesecellars@goawines.com', 'Fontainhas, Panaji, Goa'),
(24, 'Rio Wine & Spirit Merchants', '+91-20-25661122', 'merchant@riowines.co.in', 'Shivajinagar, Pune, Maharashtra'),
(25, 'Silver Oak Beverage Traders', '+91-44-28271100', 'silveroak@beveragetraders.com', 'Nungambakkam, Chennai, Tamil Nadu');

INSERT INTO wine (wine_id, wine_name, category, price, quantity, supplier_id) VALUES
(1, 'Sula Rasa Cabernet Sauvignon', 'Red Wine', 1850.00, 45, 1),
(2, 'Sula Dindori Reserve Shiraz', 'Red Wine', 1350.00, 60, 1),
(3, 'Sula Sauvignon Blanc', 'White Wine', 795.00, 80, 1),
(4, 'Sula The Source Grenache Rose', 'Rose Wine', 1050.00, 30, 1),
(5, 'Sula Brut Tropicale Sparkling', 'Sparkling Wine', 1450.00, 40, 1),
(6, 'Grover Zampa La Reserve Red', 'Red Wine', 1200.00, 55, 2),
(7, 'Grover Zampa Chene Grand Reserve', 'Red Wine', 2250.00, 25, 2),
(8, 'Grover Vijay Amritraj Reserve White', 'White Wine', 1495.00, 35, 2),
(9, 'Grover Soiree Brut Sparkling', 'Sparkling Wine', 1350.00, 20, 2),
(10, 'Fratelli Sette Flagship Red', 'Red Wine', 2100.00, 40, 3),
(11, 'Fratelli MS Red Blend', 'Red Wine', 1650.00, 50, 3),
(12, 'Fratelli Gran Cuvée Brut', 'Sparkling Wine', 1500.00, 30, 3),
(13, 'Fratelli Sangiovese Bianco', 'White Wine', 950.00, 65, 3),
(14, 'York Arros Reserve Red', 'Red Wine', 1400.00, 35, 4),
(15, 'York Sparkling Rosé', 'Sparkling Wine', 1250.00, 25, 4),
(16, 'York All-Rounder Sauvignon Blanc', 'White Wine', 750.00, 70, 4),
(17, 'KRSMA Cabernet Sauvignon Reserve', 'Red Wine', 2400.00, 15, 5),
(18, 'KRSMA Sangiovese Special Selection', 'Red Wine', 1800.00, 20, 5),
(19, 'KRSMA Sauvignon Blanc Single Vineyard', 'White Wine', 1250.00, 30, 5),
(20, 'Vallonne Malbec Reserve', 'Red Wine', 1650.00, 18, 6),
(21, 'Vallonne Vin de Passerillage Dessert', 'Dessert Wine', 1950.00, 12, 6),
(22, 'Vallonne Rose de Cabernet', 'Rose Wine', 920.00, 40, 6),
(23, 'Soma Shiraz Reserve Oak Aged', 'Red Wine', 1150.00, 45, 7),
(24, 'Soma Chenin Blanc Sec', 'White Wine', 680.00, 75, 7),
(25, 'Chandon Brut Vintage Method', 'Sparkling Wine', 1750.00, 50, 8),
(26, 'Chandon Rose Sparkling Pinot Noir', 'Sparkling Wine', 1900.00, 35, 8),
(27, 'Charosa Tempranillo Reserve', 'Red Wine', 1700.00, 28, 9),
(28, 'Charosa Selections Cabernet Shiraz', 'Red Wine', 950.00, 60, 9),
(29, 'Charosa Voignier White Wine', 'White Wine', 850.00, 40, 9),
(30, 'Reveilo Reserve Syrah Oak Aged', 'Red Wine', 1550.00, 22, 10),
(31, 'Reveilo Nero d Avola Reserve', 'Red Wine', 1450.00, 26, 10),
(32, 'Reveilo Grillo Estate White', 'White Wine', 820.00, 50, 10),
(33, 'Four Seasons Barrique Reserve Shiraz', 'Red Wine', 1300.00, 38, 11),
(34, 'Four Seasons Viognier Barrel Select', 'White Wine', 900.00, 42, 11),
(35, 'Good Earth Basso Cabernet', 'Red Wine', 1100.00, 30, 12),
(36, 'Good Earth Antaraa Shiraz Cabernet', 'Red Wine', 980.00, 35, 12),
(37, 'Big Banyan Merlot Reserve', 'Red Wine', 990.00, 55, 13),
(38, 'Big Banyan Chardonnay Dry White', 'White Wine', 890.00, 48, 13),
(39, 'Big Banyan Bellissima Late Harvest', 'Dessert Wine', 1250.00, 15, 13),
(40, 'Chateau Indage Chantilli Cabernet', 'Red Wine', 780.00, 65, 14),
(41, 'Chateau Indage Marquise de Pompadour', 'Sparkling Wine', 1200.00, 32, 14),
(42, 'Renaissance Pinot Noir Estate', 'Red Wine', 1150.00, 28, 15),
(43, 'Mokssh Sauvignon Blanc Classic', 'White Wine', 720.00, 60, 16),
(44, 'Deccan Plateau Heritage Port Wine', 'Fortified Wine', 550.00, 90, 17),
(45, 'Aarna Royal Shiraz Reserve', 'Red Wine', 1250.00, 40, 18),
(46, 'Nashik Valley Zinfandel Rose', 'Rose Wine', 760.00, 52, 19),
(47, 'Heritage Amber Sweet Dessert', 'Dessert Wine', 690.00, 35, 20),
(48, 'Chianti Classico DOCG Riserva', 'Red Wine', 3800.00, 14, 21),
(49, 'Bordeaux Medoc Chateau Blend', 'Red Wine', 4200.00, 12, 22),
(50, 'Goa Portuguese Royal Fortified Port', 'Fortified Wine', 620.00, 85, 23);

INSERT INTO customer (customer_id, customer_name, phone, email, address) VALUES
(1, 'Rajesh Sharma', '+91-9876543210', 'rajesh.sharma@gmail.com', 'Flat 402, Lotus Towers, Banjara Hills, Hyderabad'),
(2, 'Priya Patel', '+91-9823456789', 'priya.patel@yahoo.com', '12 Juhu Tara Road, Juhu, Mumbai'),
(3, 'Amit Verma', '+91-9988776655', 'amit.verma@outlook.com', 'A-45 Defense Colony, New Delhi'),
(4, 'Sneha Reddy', '+91-9849012345', 'sneha.reddy@gmail.com', 'Plot 88, Jubilee Hills, Hyderabad'),
(5, 'Vikram Malhotra', '+91-9811223344', 'vikram.m@corporateservices.in', '302 Indiranagar 100ft Road, Bengaluru'),
(6, 'Ananya Iyer', '+91-9884012345', 'ananya.iyer@gmail.com', 'B-14 Boat Club Road, R.A. Puram, Chennai'),
(7, 'Rohit Nair', '+91-9847054321', 'rohit.nair@hotmail.com', 'Green Glen Layout, Bellandur, Bengaluru'),
(8, 'Pooja Joshi', '+91-9822098765', 'pooja.joshi@gmail.com', '8 Koregaon Park South Main Road, Pune'),
(9, 'Suresh Mehta', '+91-9820011223', 'suresh.mehta@diamondexport.com', '15 Marine Drive, Nariman Point, Mumbai'),
(10, 'Deepa Deshmukh', '+91-9822334455', 'deepa.d@gmail.com', 'Flat 201, Prabhat Road, Erandwane, Pune'),
(11, 'Karthik Swaminathan', '+91-9840123456', 'karthik.swami@gmail.com', '7 Gandhi Nagar 2nd Main Road, Adyar, Chennai'),
(12, 'Sunita Agarwal', '+91-9830045678', 'sunita.agarwal@gmail.com', 'Salt Lake Sector 1, Bidhannagar, Kolkata'),
(13, 'Manoj Tiwari', '+91-9810156789', 'manoj.tiwari@veritas.in', 'C-12 Greater Kailash 1, New Delhi'),
(14, 'Kavita Rao', '+91-9849234567', 'kavita.rao@gmail.com', 'Madhapur Hitec City, Hyderabad'),
(15, 'Arjun Kapoor', '+91-9821098711', 'arjun.kapoor@gmail.com', 'Bandra West, Pali Hill, Mumbai'),
(16, 'Neha Sengupta', '+91-9831122334', 'neha.sengupta@kolkataarts.org', 'Ballygunge Circular Road, Kolkata'),
(17, 'Harish Nambiar', '+91-9845067890', 'harish.nambiar@techsol.com', 'HSR Layout Sector 3, Bengaluru'),
(18, 'Ritu Bhatt', '+91-9818877665', 'ritu.bhatt@gmail.com', 'Sector 15, Noida, Uttar Pradesh'),
(19, 'Arvind Pillai', '+91-9447012345', 'arvind.pillai@ernakulam.in', 'Panampilly Nagar, Kochi, Kerala'),
(20, 'Meenakshi Sundaram', '+91-9841023456', 'meena.sundaram@chennaitrust.org', 'Alwarpet, TTK Road, Chennai'),
(21, 'Naveen Choudhary', '+91-9829012345', 'naveen.choudhary@gmail.com', 'C-Scheme, Ashok Nagar, Jaipur, Rajasthan'),
(22, 'Divya Bansal', '+91-9814056789', 'divya.bansal@gmail.com', 'Sector 9, Chandigarh'),
(23, 'Siddharth Saxena', '+91-9826012345', 'sid.saxena@mpventure.com', 'Arera Colony E-7, Bhopal, Madhya Pradesh'),
(24, 'Tanvi Kulkarni', '+91-9823067890', 'tanvi.kulkarni@gmail.com', 'Kothrud, Paud Road, Pune, Maharashtra'),
(25, 'Gaurav Singhal', '+91-9811099887', 'gaurav.singhal@capitalgrp.in', 'DLF Phase 2, Gurugram, Haryana'),
(26, 'Shalini Menon', '+91-9846011223', 'shalini.menon@keralagold.com', 'Edappally Toll, Kochi, Kerala'),
(27, 'Aditya Singhania', '+91-9820123987', 'aditya.singhania@mumbaicorp.com', 'Altamount Road, Cumballa Hill, Mumbai'),
(28, 'Prerna Mukherjee', '+91-9830567812', 'prerna.m@gmail.com', 'Alipore Road, Kolkata, West Bengal'),
(29, 'Venkatesh Prasad', '+91-9845011992', 'venkatesh.prasad@gmail.com', 'Jayanagar 4th Block, Bengaluru'),
(30, 'Bhavna Chawla', '+91-9810456123', 'bhavna.chawla@gmail.com', 'Model Town 2, New Delhi'),
(31, 'Farhan Qureshi', '+91-9822187654', 'farhan.qureshi@photocraft.in', 'Camp Area, MG Road, Pune'),
(32, 'Simran Ahluwalia', '+91-9815098765', 'simran.ahluwalia@gmail.com', 'Ranjit Avenue, Amritsar, Punjab'),
(33, 'Kiran Kumar Reddy', '+91-9849556677', 'kirankumar.reddy@hyderabadrealty.com', 'Kondapur, Cyberabad, Hyderabad'),
(34, 'Swati Deshpande', '+91-9823190876', 'swati.deshpande@gmail.com', 'Gangapur Road, Nashik, Maharashtra'),
(35, 'Tathagata Ghosh', '+91-9831987654', 't.ghosh@bengaltrade.com', 'Park Street, Kolkata, West Bengal'),
(36, 'Nandini Hegde', '+91-9845112244', 'nandini.hegde@mangaloreports.com', 'Kadri Hills, Mangalore, Karnataka'),
(37, 'Sachin Tendulkar Jr', '+91-9820543219', 'sachin.jr@mumbaicricket.org', 'Shivaji Park, Dadar, Mumbai'),
(38, 'Pallavi Shinde', '+91-9822765432', 'pallavi.shinde@aurangabadauto.com', 'Cidco Sector N-4, Chhatrapati Sambhajinagar'),
(39, 'Ranganathan Srinivasan', '+91-9840998877', 'ranga.srini@chennaiport.org', 'Mylapore Luz Church Road, Chennai'),
(40, 'Geeta Gopinath', '+91-9447889900', 'geeta.gopinath@econanalyst.in', 'Kowdiar, Thiruvananthapuram, Kerala'),
(41, 'Aman Deep Singh', '+91-9872012345', 'amandeep.singh@punjabagro.com', 'Sarabha Nagar, Ludhiana, Punjab'),
(42, 'Rashmi Hegde', '+91-9880123987', 'rashmi.hegde@gmail.com', 'Sadashivnagar, Bengaluru, Karnataka'),
(43, 'Chetan Bhagat Rao', '+91-9820987612', 'chetan.rao@literarypub.in', 'Powai Hiranandani Gardens, Mumbai'),
(44, 'Ipsita Roy', '+91-9830112255', 'ipsita.roy@bengalart.in', 'New Town Action Area 1, Kolkata'),
(45, 'Vivek Oberoi Nair', '+91-9849887766', 'vivek.nair@gachibowli.com', 'Gachibowli Financial District, Hyderabad'),
(46, 'Monika Somani', '+91-9829123456', 'monika.somani@jaipurgems.com', 'Malviya Nagar, Jaipur, Rajasthan'),
(47, 'Raghavan Iyer', '+91-9840223344', 'raghavan.iyer@brahmancuisine.in', 'Besant Nagar, Chennai, Tamil Nadu'),
(48, 'Sanya Merchant', '+91-9820334455', 'sanya.merchant@colabashops.com', 'Colaba Causeway, Mumbai, Maharashtra'),
(49, 'Dharmendra Yadav', '+91-9415012345', 'dharmendra.yadav@upcorp.in', 'Hazratganj, Lucknow, Uttar Pradesh'),
(50, 'Zoya Akhtar Khan', '+91-9821345678', 'zoya.khan@cinemacraft.com', 'Versova Beach Road, Andheri West, Mumbai');

INSERT INTO inventory (inventory_id, wine_id, stock_quantity, reorder_level) VALUES
(1, 1, 45, 10), (2, 2, 60, 15), (3, 3, 80, 20), (4, 4, 8, 15), (5, 5, 40, 10),
(6, 6, 55, 15), (7, 7, 5, 10), (8, 8, 35, 10), (9, 9, 6, 12), (10, 10, 40, 10),
(11, 11, 50, 15), (12, 12, 30, 10), (13, 13, 65, 15), (14, 14, 35, 10), (15, 15, 7, 12),
(16, 16, 70, 20), (17, 17, 4, 10), (18, 18, 20, 10), (19, 19, 30, 10), (20, 20, 5, 10),
(21, 21, 3, 8), (22, 22, 40, 10), (23, 23, 45, 15), (24, 24, 75, 20), (25, 25, 50, 15),
(26, 26, 35, 10), (27, 27, 28, 10), (28, 28, 60, 15), (29, 29, 40, 10), (30, 30, 22, 10),
(31, 31, 26, 10), (32, 32, 50, 15), (33, 33, 38, 10), (34, 34, 42, 10), (35, 35, 30, 10),
(36, 36, 35, 10), (37, 37, 55, 15), (38, 38, 48, 12), (39, 39, 6, 10), (40, 40, 65, 15),
(41, 41, 32, 10), (42, 42, 28, 10), (43, 43, 60, 15), (44, 44, 90, 25), (45, 45, 40, 10),
(46, 46, 52, 15), (47, 47, 35, 10), (48, 48, 2, 8), (49, 49, 3, 8), (50, 50, 85, 20);

INSERT INTO orders (order_id, customer_id, order_date, total_amount, payment_status) VALUES
(1, 1, '2026-05-10 14:30:00', 3700.00, 'Paid'),
(2, 2, '2026-05-12 18:15:00', 4500.00, 'Paid'),
(3, 3, '2026-05-15 12:45:00', 2700.00, 'Paid'),
(4, 4, '2026-05-20 20:00:00', 6300.00, 'Paid'),
(5, 5, '2026-05-22 16:30:00', 3150.00, 'Paid'),
(6, 6, '2026-05-25 11:20:00', 1450.00, 'Paid'),
(7, 7, '2026-06-01 19:10:00', 4800.00, 'Paid'),
(8, 8, '2026-06-03 15:40:00', 2100.00, 'Paid'),
(9, 9, '2026-06-05 21:05:00', 7600.00, 'Paid'),
(10, 10, '2026-06-08 17:50:00', 2700.00, 'Paid'),
(11, 11, '2026-06-12 13:15:00', 3000.00, 'Paid'),
(12, 12, '2026-06-15 18:30:00', 1900.00, 'Paid'),
(13, 13, '2026-06-18 20:45:00', 5100.00, 'Paid'),
(14, 14, '2026-06-22 14:10:00', 2400.00, 'Paid'),
(15, 15, '2026-06-25 19:20:00', 4200.00, 'Paid'),
(16, 16, '2026-07-02 12:00:00', 1640.00, 'Paid'),
(17, 17, '2026-07-05 16:45:00', 3900.00, 'Paid'),
(18, 18, '2026-07-08 21:30:00', 2600.00, 'Paid'),
(19, 19, '2026-07-11 15:10:00', 1800.00, 'Paid'),
(20, 20, '2026-07-15 18:25:00', 3500.00, 'Paid'),
(21, 21, '2026-07-18 13:40:00', 2250.00, 'Pending'),
(22, 22, '2026-07-22 20:15:00', 4500.00, 'Paid'),
(23, 23, '2026-07-25 17:00:00', 2850.00, 'Paid'),
(24, 24, '2026-08-01 11:30:00', 1590.00, 'Paid'),
(25, 25, '2026-08-04 19:40:00', 6800.00, 'Paid'),
(26, 26, '2026-08-07 14:20:00', 3750.00, 'Paid'),
(27, 27, '2026-08-10 22:00:00', 8400.00, 'Paid'),
(28, 28, '2026-08-12 16:15:00', 2900.00, 'Paid'),
(29, 29, '2026-08-15 18:50:00', 4200.00, 'Paid'),
(30, 30, '2026-08-18 13:05:00', 2300.00, 'Paid'),
(31, 31, '2026-08-21 20:30:00', 3100.00, 'Paid'),
(32, 32, '2026-08-25 17:45:00', 1980.00, 'Pending'),
(33, 33, '2026-08-28 12:10:00', 5400.00, 'Paid'),
(34, 34, '2026-09-02 19:15:00', 2700.00, 'Paid'),
(35, 35, '2026-09-04 15:30:00', 3400.00, 'Paid'),
(36, 36, '2026-09-06 21:00:00', 2500.00, 'Paid'),
(37, 37, '2026-09-08 14:40:00', 4500.00, 'Paid'),
(38, 38, '2026-09-10 18:20:00', 1650.00, 'Paid'),
(39, 39, '2026-09-12 16:55:00', 2400.00, 'Paid'),
(40, 40, '2026-09-15 20:10:00', 3800.00, 'Paid'),
(41, 41, '2026-09-18 13:25:00', 2600.00, 'Paid'),
(42, 42, '2026-09-20 17:40:00', 4200.00, 'Pending'),
(43, 43, '2026-09-21 19:30:00', 3300.00, 'Paid'),
(44, 44, '2026-09-22 15:15:00', 2980.00, 'Paid'),
(45, 45, '2026-09-23 21:45:00', 5000.00, 'Paid'),
(46, 46, '2026-09-24 12:50:00', 1520.00, 'Paid'),
(47, 47, '2026-09-25 18:00:00', 2070.00, 'Paid'),
(48, 48, '2026-09-26 20:30:00', 7600.00, 'Paid'),
(49, 49, '2026-09-27 14:15:00', 3850.00, 'Paid'),
(50, 50, '2026-09-28 11:00:00', 3100.00, 'Paid');

INSERT INTO order_details (order_detail_id, order_id, wine_id, quantity, unit_price) VALUES
(1, 1, 1, 2, 1850.00), (2, 2, 7, 2, 2250.00), (3, 3, 2, 2, 1350.00), (4, 4, 10, 3, 2100.00),
(5, 5, 4, 3, 1050.00), (6, 6, 5, 1, 1450.00), (7, 7, 17, 2, 2400.00), (8, 8, 4, 2, 1050.00),
(9, 9, 48, 2, 3800.00), (10, 10, 2, 2, 1350.00), (11, 11, 12, 2, 1500.00), (12, 12, 26, 1, 1900.00),
(13, 13, 27, 3, 1700.00), (14, 14, 6, 2, 1200.00), (15, 15, 10, 2, 2100.00), (16, 16, 32, 2, 820.00),
(17, 17, 33, 3, 1300.00), (18, 18, 33, 2, 1300.00), (19, 19, 34, 2, 900.00), (20, 20, 25, 2, 1750.00),
(21, 21, 7, 1, 2250.00), (22, 22, 7, 2, 2250.00), (23, 23, 28, 3, 950.00), (24, 24, 44, 2, 550.00),
(25, 24, 47, 1, 690.00), (26, 25, 49, 1, 4200.00), (27, 25, 26, 1, 1900.00), (28, 25, 47, 1, 690.00),
(29, 26, 25, 1, 1750.00), (30, 26, 26, 1, 1900.00), (31, 27, 49, 2, 4200.00), (32, 28, 8, 1, 1495.00),
(33, 28, 14, 1, 1400.00), (34, 29, 10, 2, 2100.00), (35, 30, 23, 2, 1150.00), (36, 31, 30, 2, 1550.00),
(37, 32, 37, 2, 990.00), (38, 33, 18, 3, 1800.00), (39, 34, 2, 2, 1350.00), (40, 35, 27, 2, 1700.00),
(41, 36, 15, 2, 1250.00), (42, 37, 7, 2, 2250.00), (43, 38, 20, 1, 1650.00), (44, 39, 6, 2, 1200.00),
(45, 40, 26, 2, 1900.00), (46, 41, 33, 2, 1300.00), (47, 42, 10, 2, 2100.00), (48, 43, 11, 2, 1650.00),
(49, 44, 8, 2, 1495.00), (50, 45, 5, 2, 1450.00), (51, 45, 10, 1, 2100.00), (52, 46, 46, 2, 760.00),
(53, 47, 47, 3, 690.00), (54, 48, 48, 2, 3800.00), (55, 49, 21, 1, 1950.00), (56, 49, 26, 1, 1900.00),
(57, 50, 30, 2, 1550.00), (58, 1, 3, 1, 795.00), (59, 2, 9, 1, 1350.00), (60, 4, 13, 2, 950.00),
(61, 7, 19, 1, 1250.00), (62, 9, 22, 1, 920.00), (63, 13, 29, 2, 850.00), (64, 15, 31, 1, 1450.00),
(65, 17, 35, 1, 1100.00), (66, 20, 38, 2, 890.00), (67, 23, 40, 1, 780.00), (68, 27, 41, 1, 1200.00),
(69, 29, 43, 2, 720.00), (70, 31, 45, 1, 1250.00), (71, 33, 48, 1, 3800.00), (72, 35, 50, 2, 620.00),
(73, 37, 3, 2, 795.00), (74, 40, 16, 2, 750.00), (75, 43, 24, 2, 680.00), (76, 45, 36, 1, 980.00),
(77, 48, 17, 1, 2400.00), (78, 50, 14, 1, 1400.00), (79, 3, 16, 2, 750.00), (80, 5, 24, 1, 680.00),
(81, 8, 43, 1, 720.00), (82, 11, 46, 2, 760.00), (83, 14, 50, 2, 620.00), (84, 18, 3, 1, 795.00),
(85, 21, 44, 2, 550.00), (86, 22, 16, 2, 750.00), (87, 28, 24, 1, 680.00), (88, 30, 32, 2, 820.00),
(89, 34, 38, 1, 890.00), (90, 36, 40, 2, 780.00), (91, 39, 46, 1, 760.00), (92, 41, 50, 2, 620.00),
(93, 44, 3, 2, 795.00), (94, 47, 16, 1, 750.00), (95, 49, 24, 1, 680.00), (96, 50, 44, 2, 550.00),
(97, 6, 29, 1, 850.00), (98, 10, 34, 1, 900.00), (99, 12, 35, 1, 1100.00), (100, 16, 36, 1, 980.00),
(101, 19, 38, 1, 890.00), (102, 24, 43, 1, 720.00), (103, 32, 47, 2, 690.00), (104, 38, 50, 1, 620.00),
(105, 42, 3, 1, 795.00);

SELECT 'Complete consolidated wines_management database script executed successfully!' AS status;
