-- CampusEats SQLite Database Schema v3.0 (FINAL)
-- Fully supports RBAC, Delivery Logistics, Wallet Ledgers, and Dynamic Settings

PRAGMA foreign_keys = ON;

-- ==========================================
-- 1. SYSTEM & CONFIGURATION
-- ==========================================
CREATE TABLE Platform_Settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    description TEXT
);

-- ==========================================
-- 2. CORE & AUTHENTICATION
-- ==========================================
CREATE TABLE Campuses (
    campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    real_location_lat REAL,
    real_location_long REAL
);

CREATE TABLE Global_Admins (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE Campus_Incharges (
    incharge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campus_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    FOREIGN KEY (campus_id) REFERENCES Campuses(campus_id)
);

CREATE TABLE Students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campus_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    wallet_balance REAL DEFAULT 0.0,
    join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campus_id) REFERENCES Campuses(campus_id)
);

-- ==========================================
-- 3. LOGISTICS & PROMOTIONS (NEW)
-- ==========================================
CREATE TABLE Riders (
    rider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campus_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    vehicle_type TEXT DEFAULT 'Bike',
    current_status TEXT DEFAULT 'Available', -- 'Available', 'On Delivery', 'Offline'
    location_lat REAL,
    location_long REAL,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (campus_id) REFERENCES Campuses(campus_id)
);

CREATE TABLE Promotions (
    promo_code TEXT PRIMARY KEY,
    discount_percentage REAL NOT NULL, -- e.g., 0.20 for 20%
    max_discount_amount REAL NOT NULL, -- Cap the discount at a specific PKR
    is_active BOOLEAN DEFAULT 1
);

-- ==========================================
-- 4. VENDORS & INVENTORY
-- ==========================================
CREATE TABLE Stalls (
    stall_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campus_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    location_lat REAL,
    location_long REAL,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (campus_id) REFERENCES Campuses(campus_id)
);

CREATE TABLE Items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stall_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    selling_price REAL NOT NULL,
    cost_price REAL NOT NULL,
    image_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (stall_id) REFERENCES Stalls(stall_id)
);

-- ==========================================
-- 5. E-COMMERCE & FINANCIALS
-- ==========================================
CREATE TABLE Wallet_Transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    amount REAL NOT NULL, -- Positive for top-up, Negative for order deduction
    transaction_type TEXT NOT NULL, -- 'Top-up', 'Order Payment', 'Refund'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Students(student_id)
);

CREATE TABLE Carts (
    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    stall_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Students(student_id),
    FOREIGN KEY (stall_id) REFERENCES Stalls(stall_id)
);

CREATE TABLE Cart_Items (
    cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (cart_id) REFERENCES Carts(cart_id),
    FOREIGN KEY (item_id) REFERENCES Items(item_id)
);

CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    stall_id INTEGER NOT NULL,
    rider_id INTEGER, -- NEW: Can be NULL if order_type is 'Pickup'
    order_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    order_type TEXT NOT NULL,
    
    subtotal REAL NOT NULL,
    promo_code TEXT, -- NEW: Links to Promotions
    discount_amount REAL DEFAULT 0.0,
    gst_amount REAL NOT NULL,
    tip_amount REAL DEFAULT 0.0,
    total_amount REAL NOT NULL,
    
    payment_method TEXT NOT NULL,
    payment_status TEXT NOT NULL DEFAULT 'Pending',
    delivery_status TEXT NOT NULL,
    cancel_reason TEXT,
    
    FOREIGN KEY (student_id) REFERENCES Students(student_id),
    FOREIGN KEY (stall_id) REFERENCES Stalls(stall_id),
    FOREIGN KEY (rider_id) REFERENCES Riders(rider_id),
    FOREIGN KEY (promo_code) REFERENCES Promotions(promo_code)
);

CREATE TABLE Order_Items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (item_id) REFERENCES Items(item_id)
);

CREATE TABLE Reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_id INTEGER,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    review_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (item_id) REFERENCES Items(item_id)
);

-- ==========================================
-- 6. PERFORMANCE INDEXES
-- ==========================================
CREATE INDEX idx_orders_time ON Orders(order_time);
CREATE INDEX idx_orders_stall ON Orders(stall_id);
CREATE INDEX idx_orders_rider ON Orders(rider_id);
CREATE INDEX idx_wallet_student ON Wallet_Transactions(student_id);
