-- CampusEats Database Migrations v3.1
-- Adds new fields while maintaining backward compatibility with existing Streamlit dashboard

-- =========================================
-- Migration 1: Add avg_prep_time_minutes to Stalls
-- =========================================
-- Default to 15 minutes for existing stalls
ALTER TABLE Stalls ADD COLUMN avg_prep_time_minutes INTEGER DEFAULT 15;

-- =========================================
-- Migration 2: Add rider_rating and rider_comment to Reviews
-- =========================================
-- These allow customers to rate their delivery experience separately from food quality
ALTER TABLE Reviews ADD COLUMN rider_rating INTEGER CHECK(rider_rating >= 1 AND rider_rating <= 5) DEFAULT NULL;
ALTER TABLE Reviews ADD COLUMN rider_comment TEXT DEFAULT NULL;

-- =========================================
-- Migration 3: Create Order_Status_Logs table
-- =========================================
-- Granular tracking of order status changes (for future consumer app)
-- Preserves delivery_status column in Orders for dashboard compatibility
CREATE TABLE Order_Status_Logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
);

-- Index for performance when querying status logs for an order
CREATE INDEX idx_order_status_logs_order ON Order_Status_Logs(order_id);
CREATE INDEX idx_order_status_logs_timestamp ON Order_Status_Logs(timestamp);

-- =========================================
-- Populate Order_Status_Logs from existing Orders
-- =========================================
-- Create an initial status log entry for each order based on its delivery_status
INSERT INTO Order_Status_Logs (order_id, status, timestamp, notes)
SELECT 
    order_id,
    delivery_status,
    order_time,
    'Initial status from order creation'
FROM Orders;

-- For canceled orders, add a second log entry
INSERT INTO Order_Status_Logs (order_id, status, timestamp, notes)
SELECT 
    order_id,
    'Canceled',
    datetime(order_time, '+1 minute'),
    'Order canceled - Reason: ' || COALESCE(cancel_reason, 'Unknown')
FROM Orders
WHERE delivery_status = 'Canceled';
