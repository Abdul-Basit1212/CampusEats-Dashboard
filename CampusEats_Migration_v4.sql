-- ==========================================
-- CampusEats Database Migration v4.0
-- Safe Extension for Student Consumer App
-- ==========================================
-- This migration extends the existing schema WITHOUT breaking dashboard compatibility
-- ✅ Rule: NO table drops, NO column renames, NO constraint removals
-- ✅ Rule: Only ADD new columns and CREATE new tables

PRAGMA foreign_keys = ON;

-- ==========================================
-- 1. ALTER ORDERS TABLE - ADD NEW COLUMNS
-- ==========================================
-- Add delivery fee support
ALTER TABLE Orders ADD COLUMN delivery_fee REAL DEFAULT 0;

-- Add enhanced payment gateway support (Stripe, Cash, Card, COD, Card_on_Delivery, Wallet)
ALTER TABLE Orders ADD COLUMN payment_gateway TEXT DEFAULT 'Cash';

-- ==========================================
-- 2. ALTER STALLS TABLE - ADD IMAGE SUPPORT
-- ==========================================
-- Add logo URL for stall branding
ALTER TABLE Stalls ADD COLUMN logo_url TEXT;

-- Add banner URL for stall branding
ALTER TABLE Stalls ADD COLUMN banner_url TEXT;

-- ==========================================
-- 3. CREATE DISCOUNT_BREAKDOWN TABLE
-- ==========================================
-- Supports stacked discounts: promo + game + deal
-- Multiple rows per order allowed
-- Backend enforces: Total discount ≤ 30% of subtotal
CREATE TABLE Discount_Breakdown (
    discount_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    discount_type TEXT NOT NULL, -- 'promo', 'game', 'deal'
    discount_percentage REAL NOT NULL,
    discount_amount REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES Orders(order_id)
);

-- Index for fast discount lookup by order
CREATE INDEX idx_discount_order ON Discount_Breakdown(order_id);

-- ==========================================
-- 4. CREATE GAME_REWARDS TABLE
-- ==========================================
-- Tracks game-based discount rewards earned by students
CREATE TABLE Game_Rewards (
    reward_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    order_id INTEGER,
    score INTEGER NOT NULL DEFAULT 0,
    discount_percentage REAL NOT NULL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES Students(student_id),
    FOREIGN KEY(order_id) REFERENCES Orders(order_id)
);

-- Index for fast reward lookup by student
CREATE INDEX idx_game_reward_student ON Game_Rewards(student_id);

-- Index for reward lookup by order
CREATE INDEX idx_game_reward_order ON Game_Rewards(order_id);

-- ==========================================
-- 5. CREATE AI_COMBOS TABLE
-- ==========================================
-- Tracks item pair frequency for AI recommendations
-- Example: "Users who order Biryani often order Lassi"
CREATE TABLE AI_Combos (
    combo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_1_id INTEGER NOT NULL,
    item_2_id INTEGER NOT NULL,
    frequency INTEGER DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(item_1_id) REFERENCES Items(item_id),
    FOREIGN KEY(item_2_id) REFERENCES Items(item_id)
);

-- Index for fast combo lookup
CREATE INDEX idx_ai_combo_item1 ON AI_Combos(item_1_id);
CREATE INDEX idx_ai_combo_item2 ON AI_Combos(item_2_id);

-- ==========================================
-- 6. VALIDATION NOTES
-- ==========================================
-- ✅ SAFE: All existing tables and columns remain unchanged
-- ✅ SAFE: Only new columns added with DEFAULT values (backward compatible)
-- ✅ SAFE: New tables don't interfere with dashboard queries
-- ✅ SAFE: Foreign keys maintain referential integrity
-- ✅ SAFE: Indexes added for performance (no schema breaking change)
--
-- Multi-Stall Orders:
-- - Orders.stall_id kept as "primary stall" (first item's stall)
-- - Order_Items allows items from multiple stalls
-- - Dashboard queries unaffected (still uses Orders.stall_id for reporting)
--
-- Delivery Fee:
-- - Stored separately in Orders.delivery_fee
-- - Original discount_amount and total_amount remain unchanged
-- - Backend calculates: final_total = subtotal - discounts + gst + delivery_fee + tip
--
-- Stacked Discounts:
-- - Discount_Breakdown allows multiple discount rows per order
-- - Original promo_code and discount_amount still used by dashboard
-- - New table used by consumer app for detailed breakdown
--
-- Game Rewards & AI Combos:
-- - Purely new features, don't affect existing queries
-- - Consumer app uses these; dashboard ignores them
-- ==========================================
