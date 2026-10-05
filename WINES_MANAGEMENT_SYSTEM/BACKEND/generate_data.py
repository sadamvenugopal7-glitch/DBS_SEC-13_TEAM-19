"""
Dataset Generator for Wines Management System.
Generates 250 customers, 25 suppliers, 50 wines, 50 inventory records,
100 orders, and 200+ order details with exact referential integrity.
"""

import csv
import os
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "database")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# 1. SUPPLIERS (25)
suppliers = [
    ("Sula Vineyards Ltd", "+91-253-2297200", "orders@sulawines.com", "Govardhan Village, Gangapur Dam Road, Nashik, Maharashtra"),
    ("Grover Zampa Vineyards", "+91-80-27622826", "sales@groverzampa.com", "Raghunathapur, Doddaballapur Road, Bengaluru, Karnataka"),
    ("Fratelli Wines Pvt Ltd", "+91-218-4228000", "contact@fratelliwines.in", "Akluj, Solapur District, Maharashtra"),
    ("York Winery & Tasting Room", "+91-253-2230700", "info@yorkwinery.com", "Gangavarhe Village, Gangapur Dam, Nashik, Maharashtra"),
    ("KRSMA Estates Vineyard", "+91-83-94240500", "cellar@krsmaestates.com", "Hampi Hills, Koppal District, Karnataka"),
    ("Vallonne Vineyards Boutique", "+91-9769138346", "enquiry@vallonnevineyards.com", "Kavnai, Igatpuri, Nashik, Maharashtra"),
    ("Soma Vine Village", "+91-7028065001", "reservations@somavinevillage.com", "Village Ganghavare, Gangapur-Savargaon Road, Nashik"),
    ("Domaine Chandon India", "+91-253-3049100", "chandonservice@chandon.co.in", "Dindori, Nashik District, Maharashtra"),
    ("Charosa Wineries Ltd", "+91-22-67097777", "orders@charosawineries.com", "Charosa Village, Dindori Taluka, Nashik, Maharashtra"),
    ("Vintage Wines (Reveilo)", "+91-255-6258010", "reveilo@vintagewines.co.in", "Niphad, Nashik District, Maharashtra"),
    ("Four Seasons Vineyards", "+91-211-2244200", "cellar@fourseasonsvineyards.com", "Rangaon, Daund Taluka, Pune District, Maharashtra"),
    ("Good Earth Winery Co", "+91-253-2341200", "sales@goodearthwinery.com", "Vinchur Wine Park, Nashik, Maharashtra"),
    ("Big Banyan Wines Ltd", "+91-80-41235678", "contact@bigbanyanwines.com", "Kalyanipura, Nelamangala Taluk, Bengaluru Rural"),
    ("Chateau Indage Heritage", "+91-211-4237100", "heritage@chateauindage.com", "Narayangaon, Pune District, Maharashtra"),
    ("Renaissance Winery Nashik", "+91-253-2415500", "sales@renaissancewinery.net", "Ozar, Nashik-Agra Highway, Maharashtra"),
    ("Mokssh Vineyards India", "+91-253-6691234", "info@moksshwines.com", "Dindori Valley, Nashik, Maharashtra"),
    ("Deccan Plateau Cellars", "+91-83-22741200", "info@deccanplateau.in", "Bilekallu Village, Bijapur District, Karnataka"),
    ("Aarna Wine Distributors", "+91-40-23351299", "aarnawines@distributors.com", "Banjara Hills Road No 12, Hyderabad, Telangana"),
    ("Nashik Valley Estates", "+91-253-2570088", "sales@nashikvalley.com", "MIDC Ambad, Nashik, Maharashtra"),
    ("Heritage Grape Winery", "+91-80-22214455", "heritage@grapewinery.in", "Kengeri Satellite Town, Bengaluru, Karnataka"),
    ("Tuscan Heritage Importers", "+91-22-40019900", "import@tuscanheritage.com", "Worli Seaface, Mumbai, Maharashtra"),
    ("Bordeaux Selections India", "+91-11-41527788", "contact@bordeauxselections.in", "Connaught Place, New Delhi"),
    ("Goa Portuguese Cellars", "+91-832-2431200", "portuguesecellars@goawines.com", "Fontainhas, Panaji, Goa"),
    ("Rio Wine & Spirit Merchants", "+91-20-25661122", "merchant@riowines.co.in", "Shivajinagar, Pune, Maharashtra"),
    ("Silver Oak Beverage Traders", "+91-44-28271100", "silveroak@beveragetraders.com", "Nungambakkam, Chennai, Tamil Nadu")
]

# 2. WINES (50)
wines = [
    (1, "Sula Rasa Cabernet Sauvignon", "Red Wine", 1850.00, 45, 1, "Complex full-bodied red aged in French oak barrels with hints of dark cocoa and berries."),
    (2, "Sula Dindori Reserve Shiraz", "Red Wine", 1350.00, 60, 1, "Lush and aromatic with aromas of crushed black pepper and ripe blackberries."),
    (3, "Sula Sauvignon Blanc", "White Wine", 795.00, 80, 1, "Crisp dry white with herbaceous notes, green peppers, and refreshing citrus."),
    (4, "Sula The Source Grenache Rose", "Rose Wine", 1050.00, 8, 1, "Bright coral blush wine with delicate aromas of citrus and fresh strawberries."),
    (5, "Sula Brut Tropicale Sparkling", "Sparkling Wine", 1450.00, 40, 1, "Method traditional sparkling rosé with refreshing fruit character."),
    (6, "Grover Zampa La Reserve Red", "Red Wine", 1200.00, 55, 2, "Iconic blend of Cabernet Sauvignon and Shiraz with chocolate and vanilla notes."),
    (7, "Grover Zampa Chene Grand Reserve", "Red Wine", 2250.00, 5, 2, "Aged for 15 months in French oak barrels; concentrated dark fruit and spice."),
    (8, "Grover Vijay Amritraj Reserve White", "White Wine", 1495.00, 35, 2, "Viognier blend with peach, honey, and floral jasmine aromas."),
    (9, "Grover Soiree Brut Sparkling", "Sparkling Wine", 1350.00, 6, 2, "Creamy texture with fine perlage and aromas of brioche and green apple."),
    (10, "Fratelli Sette Flagship Red", "Red Wine", 2100.00, 40, 3, "Super-Tuscan style blend of Sangiovese and Cabernet Franc with velvety tannins."),
    (11, "Fratelli MS Red Blend", "Red Wine", 1650.00, 50, 3, "Created with master sommelier Steven Spurrier; rich plum and cedar notes."),
    (12, "Fratelli Gran Cuvee Brut", "Sparkling Wine", 1500.00, 30, 3, "Zero dosage traditional method sparkling wine with crisp acidity."),
    (13, "Fratelli Sangiovese Bianco", "White Wine", 950.00, 65, 3, "Rare white wine vinified from red Sangiovese grapes with crisp pear aroma."),
    (14, "York Arros Reserve Red", "Red Wine", 1400.00, 35, 4, "Flagship blend of Shiraz and Cabernet Sauvignon aged in American and French oak."),
    (15, "York Sparkling Rose", "Sparkling Wine", 1250.00, 7, 4, "100% Chenin Blanc & Shiraz sparkling wine made in traditional méthode champenoise."),
    (16, "York All-Rounder Sauvignon Blanc", "White Wine", 750.00, 70, 4, "Tropical fruit flavors of passionfruit, guava, and flinty minerality."),
    (17, "KRSMA Cabernet Sauvignon Reserve", "Red Wine", 2400.00, 4, 5, "Cult wine from Hampi Hills with cassis, dark plum, and tobacco complexity."),
    (18, "KRSMA Sangiovese Special Selection", "Red Wine", 1800.00, 20, 5, "Bright cherry fruit with high natural acidity and subtle sweet spices."),
    (19, "KRSMA Sauvignon Blanc Single Vineyard", "White Wine", 1250.00, 30, 5, "Flinty, elegant, and crisp with citrus peel and gooseberry accents."),
    (20, "Vallonne Malbec Reserve", "Red Wine", 1650.00, 5, 6, "India's first single-varietal Malbec with blackberry, violet, and dark oak flavors."),
    (21, "Vallonne Vin de Passerillage Dessert", "Dessert Wine", 1950.00, 3, 6, "Naturally sweet dessert wine with dried apricot and honeyed notes."),
    (22, "Vallonne Rose de Cabernet", "Rose Wine", 920.00, 40, 6, "Dry rosé from Cabernet Sauvignon grapes with raspberry and rose petal nose."),
    (23, "Soma Shiraz Reserve Oak Aged", "Red Wine", 1150.00, 45, 7, "Smooth, medium-bodied red wine with soft tannins and red currant flavors."),
    (24, "Soma Chenin Blanc Sec", "White Wine", 680.00, 75, 7, "Off-dry white with refreshing notes of green apples, pineapple, and citrus."),
    (25, "Chandon Brut Vintage Method", "Sparkling Wine", 1750.00, 50, 8, "Classic sparkling blend of Chenin Blanc, Chardonnay, and Pinot Noir."),
    (26, "Chandon Rose Sparkling Pinot Noir", "Sparkling Wine", 1900.00, 35, 8, "Elegant salmon pink sparkler with cherry, strawberry, and brioche aromas."),
    (27, "Charosa Tempranillo Reserve", "Red Wine", 1700.00, 28, 9, "Warm coconut and vanilla bouquet paired with rich dark berry concentration."),
    (28, "Charosa Selections Cabernet Shiraz", "Red Wine", 950.00, 60, 9, "Balanced ruby red blend with ripe berries and subtle peppery spice."),
    (29, "Charosa Voignier White Wine", "White Wine", 850.00, 40, 9, "Exotic aromatics of apricot, honeysuckle, and almond flower."),
    (30, "Reveilo Reserve Syrah Oak Aged", "Red Wine", 1550.00, 22, 10, "Aged in French oak for 12 months; powerful red berry fruit and peppery finish."),
    (31, "Reveilo Nero d Avola Reserve", "Red Wine", 1450.00, 26, 10, "Unique Sicilian grape grown in Nashik with sweet cherries and balsamic notes."),
    (32, "Reveilo Grillo Estate White", "White Wine", 820.00, 50, 10, "Fresh Mediterranean varietal with citrus blossom and crisp acidity."),
    (33, "Four Seasons Barrique Reserve Shiraz", "Red Wine", 1300.00, 38, 11, "Aged in new oak barrels; full-bodied with notes of ripe plums and dark chocolate."),
    (34, "Four Seasons Viognier Barrel Select", "White Wine", 900.00, 42, 11, "Aromatic white offering peach, lychee, and fresh floral notes."),
    (35, "Good Earth Basso Cabernet", "Red Wine", 1100.00, 30, 12, "Earthy and savoury Cabernet Sauvignon with structured tannins."),
    (36, "Good Earth Antaraa Shiraz Cabernet", "Red Wine", 980.00, 35, 12, "Harmonious blend with soft tannins and red plum flavors."),
    (37, "Big Banyan Merlot Reserve", "Red Wine", 990.00, 55, 13, "Plush and round red with sweet red fruit, cocoa, and gentle vanilla oak."),
    (38, "Big Banyan Chardonnay Dry White", "White Wine", 890.00, 48, 13, "Lightly wooded white with green apple, butterscotch, and citrus finish."),
    (39, "Big Banyan Bellissima Late Harvest", "Dessert Wine", 1250.00, 6, 13, "Luscious sweet wine made from late-harvest Muscat grapes."),
    (40, "Chateau Indage Chantilli Cabernet", "Red Wine", 780.00, 65, 14, "Historic Indian table wine with soft red fruit and easy-drinking style."),
    (41, "Chateau Indage Marquise de Pompadour", "Sparkling Wine", 1200.00, 32, 14, "Crisp sparkling wine with delicate bubbles and citrus peel notes."),
    (42, "Renaissance Pinot Noir Estate", "Red Wine", 1150.00, 28, 15, "Light-bodied ruby red with cranberry, cherry, and forest floor complexity."),
    (43, "Mokssh Sauvignon Blanc Classic", "White Wine", 720.00, 60, 16, "Fresh grassy bouquet with grapefruit, lime, and mineral backbone."),
    (44, "Deccan Plateau Heritage Port Wine", "Fortified Wine", 550.00, 90, 17, "Sweet fortified wine with rich caramel, raisin, and dried fruit flavors."),
    (45, "Aarna Royal Shiraz Reserve", "Red Wine", 1250.00, 40, 18, "Robust Deccan Shiraz with spiced blackberry and toasted oak aromas."),
    (46, "Nashik Valley Zinfandel Rose", "Rose Wine", 760.00, 52, 19, "Semi-sweet refreshing rosé with bright strawberry and watermelon flavors."),
    (47, "Heritage Amber Sweet Dessert", "Dessert Wine", 690.00, 35, 20, "Golden amber dessert wine with candied orange peel and floral honey."),
    (48, "Chianti Classico DOCG Riserva", "Red Wine", 3800.00, 2, 21, "Imported Italian Tuscan red with tart cherry, leather, and dried oregano."),
    (49, "Bordeaux Medoc Chateau Blend", "Red Wine", 4200.00, 3, 22, "Classic French Left Bank Cabernet-Merlot with cassis and graphite notes."),
    (50, "Goa Portuguese Royal Fortified Port", "Fortified Wine", 620.00, 85, 23, "Traditional Goan fortified wine with sweet raisin and warm spice notes.")
]

# 3. GENERATE 250 REALISTIC FICTIONAL CUSTOMERS
first_names = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Atharv", "Advik", "Pranav", "Kabir", "Ananya", "Diya", "Ira", "Myra", "Saanvi",
    "Aanya", "Pari", "Riya", "Aadhya", "Kiara", "Sneha", "Pooja", "Priya", "Neha", "Kavita",
    "Rajesh", "Amit", "Vikram", "Rohit", "Suresh", "Manoj", "Harish", "Arvind", "Naveen", "Gaurav",
    "Deepa", "Sunita", "Ritu", "Divya", "Tanvi", "Shalini", "Prerna", "Bhavna", "Swati", "Nandini"
]

last_names = [
    "Sharma", "Verma", "Reddy", "Patel", "Kumar", "Iyer", "Nair", "Joshi", "Mehta", "Deshmukh",
    "Swaminathan", "Agarwal", "Tiwari", "Rao", "Kapoor", "Sengupta", "Nambiar", "Bhatt", "Pillai", "Sundaram",
    "Choudhary", "Bansal", "Saxena", "Kulkarni", "Singhal", "Menon", "Singhania", "Mukherjee", "Prasad", "Chawla",
    "Qureshi", "Ahluwalia", "Deshpande", "Ghosh", "Hegde", "Shinde", "Srinivasan", "Gopinath", "Singh", "Somani",
    "Iyer", "Merchant", "Yadav", "Khan", "Dubey", "Mishra", "Pandey", "Tripathi", "Shukla", "Bose"
]

cities = [
    ("Hyderabad", "Banjara Hills, Jubilee Hills, Madhapur, Gachibowli, Kondapur"),
    ("Bengaluru", "Indiranagar, Koramangala, HSR Layout, Whitefield, Jayanagar"),
    ("Mumbai", "Bandra West, Juhu, Colaba, Worli, Powai"),
    ("New Delhi", "Defense Colony, Greater Kailash, Connaught Place, Vasant Kunj"),
    ("Pune", "Koregaon Park, Kothrud, Kalyani Nagar, Viman Nagar"),
    ("Chennai", "Adyar, Mylapore, Alwarpet, Besant Nagar, Boat Club"),
    ("Kolkata", "Salt Lake, Ballygunge, Park Street, Alipore, New Town"),
    ("Goa", "Panaji, Candolim, Calangute, Margao"),
    ("Nashik", "Gangapur Road, College Road, Mahatma Nagar, Indira Nagar"),
    ("Chandigarh", "Sector 9, Sector 17, Sector 35, Sector 8")
]

random.seed(42)

customers = []
for i in range(1, 251):
    fname = first_names[(i - 1) % len(first_names)]
    lname = last_names[(i * 7) % len(last_names)]
    name = f"{fname} {lname}"
    phone = f"+91-98{random.randint(10000000, 99999999)}"
    email = f"{fname.lower()}.{lname.lower()}{i}@samplemail.com"
    city, areas = cities[i % len(cities)]
    area = random.choice([a.strip() for a in areas.split(",")])
    address = f"Flat {random.randint(101, 909)}, {area}, {city}"
    customers.append((i, name, phone, email, address))

# 4. INVENTORY (50)
inventory = []
for w in wines:
    w_id = w[0]
    stock_qty = w[4]
    reorder_lvl = 10 if stock_qty > 10 else 15
    inventory.append((w_id, w_id, stock_qty, reorder_lvl))

# 5. ORDERS (100) & ORDER DETAILS (200+)
orders = []
order_details = []
detail_id_counter = 1
start_date = datetime(2026, 4, 1, 10, 0, 0)

for o_id in range(1, 101):
    c_id = random.randint(1, 250)
    o_date = start_date + timedelta(days=o_id * 1.5, hours=random.randint(1, 10), minutes=random.randint(0, 59))
    status = "Paid" if random.random() < 0.85 else "Pending"
    
    # 2 to 3 wine items per order
    num_items = random.randint(2, 3)
    chosen_wines = random.sample(wines, num_items)
    
    order_total = 0.0
    for w in chosen_wines:
        qty = random.randint(1, 3)
        unit_p = float(w[3])
        line_sub = qty * unit_p
        order_total += line_sub
        order_details.append((detail_id_counter, o_id, w[0], qty, unit_p, line_sub))
        detail_id_counter += 1

    orders.append((o_id, c_id, o_date.strftime("%Y-%m-%d %H:%M:%S"), round(order_total, 2), status))

# ==============================================================
# WRITE CSV FILES
# ==============================================================

# Customers CSV
with open(os.path.join(DATA_DIR, "customers.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["customer_id", "customer_name", "phone", "email", "address", "created_at"])
    for c in customers:
        writer.writerow([c[0], c[1], c[2], c[3], c[4], "2026-04-01 10:00:00"])

# Suppliers CSV
with open(os.path.join(DATA_DIR, "suppliers.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["supplier_id", "supplier_name", "phone", "email", "address"])
    for idx, s in enumerate(suppliers, 1):
        writer.writerow([idx, s[0], s[1], s[2], s[3]])

# Wines CSV
with open(os.path.join(DATA_DIR, "wines.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["wine_id", "wine_name", "category", "price", "quantity", "supplier_id", "description"])
    for w in wines:
        writer.writerow([w[0], w[1], w[2], w[3], w[4], w[5], w[6]])

# Inventory CSV
with open(os.path.join(DATA_DIR, "inventory.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["inventory_id", "wine_id", "stock_quantity", "reorder_level"])
    for inv in inventory:
        writer.writerow([inv[0], inv[1], inv[2], inv[3]])

# Orders CSV
with open(os.path.join(DATA_DIR, "orders.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["order_id", "customer_id", "order_date", "total_amount", "payment_status"])
    for o in orders:
        writer.writerow([o[0], o[1], o[2], o[3], o[4]])

# Order Details CSV
with open(os.path.join(DATA_DIR, "order_details.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["order_detail_id", "order_id", "wine_id", "quantity", "unit_price", "subtotal"])
    for od in order_details:
        writer.writerow([od[0], od[1], od[2], od[3], od[4], od[5]])

print(f"[OK] Generated {len(customers)} customers, {len(suppliers)} suppliers, {len(wines)} wines, {len(inventory)} inventory, {len(orders)} orders, {len(order_details)} order details in data/")

# ==============================================================
# WRITE database/03_insert_sample_data.sql
# ==============================================================
with open(os.path.join(DB_DIR, "03_insert_sample_data.sql"), "w", encoding="utf-8") as f:
    f.write("-- =====================================================================\n")
    f.write("-- WINES MANAGEMENT SYSTEM - SAMPLE DATASET\n")
    f.write(f"-- 25 Suppliers, 50 Wines, {len(customers)} Customers, 50 Inventory, {len(orders)} Orders, {len(order_details)} Details\n")
    f.write("-- Database: wines_management_db\n")
    f.write("-- File: 03_insert_sample_data.sql\n")
    f.write("-- =====================================================================\n\n")
    f.write("USE wines_management_db;\n\n")

    # Suppliers
    f.write("-- 1. INSERT SUPPLIERS (25)\n")
    f.write("INSERT INTO supplier (supplier_id, supplier_name, phone, email, address) VALUES\n")
    sup_rows = [f"({i}, '{s[0]}', '{s[1]}', '{s[2]}', '{s[3]}')" for i, s in enumerate(suppliers, 1)]
    f.write(",\n".join(sup_rows) + ";\n\n")

    # Wines
    f.write("-- 2. INSERT WINES (50)\n")
    f.write("INSERT INTO wine (wine_id, wine_name, category, price, quantity, supplier_id, description) VALUES\n")
    wine_rows = [f"({w[0]}, '{w[1]}', '{w[2]}', {w[3]}, {w[4]}, {w[5]}, '{w[6].replace("'", "''")}')" for w in wines]
    f.write(",\n".join(wine_rows) + ";\n\n")

    # Customers (250)
    f.write(f"-- 3. INSERT CUSTOMERS ({len(customers)})\n")
    f.write("INSERT INTO customer (customer_id, customer_name, phone, email, address) VALUES\n")
    cust_rows = [f"({c[0]}, '{c[1]}', '{c[2]}', '{c[3]}', '{c[4].replace("'", "''")}')" for c in customers]
    f.write(",\n".join(cust_rows) + ";\n\n")

    # Inventory (50)
    f.write("-- 4. INSERT INVENTORY (50)\n")
    f.write("INSERT INTO inventory (inventory_id, wine_id, stock_quantity, reorder_level) VALUES\n")
    inv_rows = [f"({inv[0]}, {inv[1]}, {inv[2]}, {inv[3]})" for inv in inventory]
    f.write(",\n".join(inv_rows) + ";\n\n")

    # Orders (100)
    f.write(f"-- 5. INSERT ORDERS ({len(orders)})\n")
    f.write("INSERT INTO orders (order_id, customer_id, order_date, total_amount, payment_status) VALUES\n")
    order_rows = [f"({o[0]}, {o[1]}, '{o[2]}', {o[3]}, '{o[4]}')" for o in orders]
    f.write(",\n".join(order_rows) + ";\n\n")

    # Order Details (200+)
    f.write(f"-- 6. INSERT ORDER_DETAILS ({len(order_details)})\n")
    f.write("INSERT INTO order_details (order_detail_id, order_id, wine_id, quantity, unit_price) VALUES\n")
    od_rows = [f"({od[0]}, {od[1]}, {od[2]}, {od[3]}, {od[4]})" for od in order_details]
    f.write(",\n".join(od_rows) + ";\n\n")

    f.write("SELECT 'Sample dataset loaded: 25 suppliers, 50 wines, 250 customers, 50 inventory, 100 orders, 200+ details!' AS status;\n")

print(f"[OK] Generated database/03_insert_sample_data.sql with {len(customers)} customers, {len(orders)} orders, and {len(order_details)} line items!")
