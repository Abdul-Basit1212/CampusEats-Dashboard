# CampusEats Database v4.0 - Developer Quick Reference

## 🎯 New Database Features at a Glance

### 1. Multi-Stall Orders
```sql
-- Get all items from an order (might be from multiple stalls)
SELECT oi.item_id, i.name, i.stall_id, oi.quantity, oi.unit_price
FROM Order_Items oi
JOIN Items i ON oi.item_id = i.item_id
WHERE oi.order_id = ?;

-- Get stall from order (primary stall)
SELECT s.* FROM Stalls s WHERE s.stall_id = (
    SELECT stall_id FROM Orders WHERE order_id = ?
);
```

### 2. Delivery Fees
```sql
-- Calculate order total with delivery fee
SELECT 
    subtotal,
    discount_amount,
    gst_amount,
    delivery_fee,  -- NEW
    tip_amount,
    (subtotal - discount_amount + gst_amount + delivery_fee + tip_amount) as total_amount
FROM Orders
WHERE order_id = ?;
```

### 3. Stacked Discounts
```sql
-- Get all discount sources for an order
SELECT 
    discount_type,
    discount_percentage,
    discount_amount,
    created_at
FROM Discount_Breakdown
WHERE order_id = ?
ORDER BY created_at;

-- Total discount (should validate ≤ 30% of subtotal)
SELECT SUM(discount_amount) as total_discount
FROM Discount_Breakdown
WHERE order_id = ?;
```

### 4. Game Rewards
```sql
-- Get student's current game rewards
SELECT 
    reward_id,
    score,
    discount_percentage,
    created_at,
    order_id
FROM Game_Rewards
WHERE student_id = ?
ORDER BY created_at DESC;

-- Get all-time game score for student
SELECT SUM(score) as total_score FROM Game_Rewards WHERE student_id = ?;
```

### 5. AI Combo Recommendations
```sql
-- Get "frequently bought together" for item
SELECT 
    CASE 
        WHEN item_1_id = ? THEN item_2_id
        WHEN item_2_id = ? THEN item_1_id
    END as recommended_item_id,
    frequency
FROM AI_Combos
WHERE (item_1_id = ? OR item_2_id = ?)
  AND frequency >= 2
ORDER BY frequency DESC
LIMIT 5;

-- Get recommended items as full details
SELECT i.*, ai.frequency
FROM AI_Combos ai
JOIN Items i ON (
    CASE 
        WHEN ai.item_1_id = ? THEN i.item_id = ai.item_2_id
        WHEN ai.item_2_id = ? THEN i.item_id = ai.item_1_id
    END
)
WHERE (ai.item_1_id = ? OR ai.item_2_id = ?)
ORDER BY ai.frequency DESC
LIMIT 5;
```

### 6. Payment Gateway Routing
```sql
-- Get orders by payment gateway
SELECT order_id, payment_gateway, total_amount
FROM Orders
WHERE payment_gateway = 'Stripe'  -- or 'Wallet', 'COD', etc.
AND delivery_status = 'Completed';

-- Map payment method to gateway
SELECT DISTINCT payment_method, payment_gateway
FROM Orders
WHERE student_id = ?;
```

### 7. Rider Assignment
```sql
-- Get available riders for campus
SELECT rider_id, name, location_lat, location_long
FROM Riders
WHERE campus_id = ? AND current_status = 'Available';

-- Get orders assigned to rider
SELECT o.order_id, o.order_time, o.total_amount, s.name as stall_name
FROM Orders o
JOIN Stalls s ON o.stall_id = s.stall_id
WHERE o.rider_id = ?
AND o.delivery_status IN ('Placed', 'Completed');
```

### 8. Stall Branding
```sql
-- Get stall with branding
SELECT stall_id, name, logo_url, banner_url, location_lat, location_long
FROM Stalls
WHERE stall_id = ?;

-- Get all stalls with logos
SELECT stall_id, name, logo_url, category
FROM Stalls
WHERE logo_url IS NOT NULL;
```

---

## 📊 Common Queries

### Order Summary with All New Fields
```sql
SELECT 
    o.order_id,
    o.student_id,
    s.name as student_name,
    o.stall_id,
    st.name as stall_name,
    o.order_type,
    o.order_time,
    o.subtotal,
    o.discount_amount,
    o.delivery_fee,      -- NEW
    o.gst_amount,
    o.tip_amount,
    o.total_amount,
    o.payment_method,
    o.payment_gateway,   -- NEW
    o.delivery_status,
    o.rider_id,
    r.name as rider_name,
    COUNT(oi.item_id) as item_count
FROM Orders o
LEFT JOIN Students s ON o.student_id = s.student_id
LEFT JOIN Stalls st ON o.stall_id = st.stall_id
LEFT JOIN Riders r ON o.rider_id = r.rider_id
LEFT JOIN Order_Items oi ON o.order_id = oi.order_id
WHERE o.order_id = ?
GROUP BY o.order_id;
```

### Discount Breakdown Report
```sql
SELECT 
    o.order_id,
    o.subtotal,
    SUM(CASE WHEN db.discount_type = 'promo' THEN db.discount_amount ELSE 0 END) as promo_discount,
    SUM(CASE WHEN db.discount_type = 'game' THEN db.discount_amount ELSE 0 END) as game_discount,
    SUM(db.discount_amount) as total_discount,
    CAST(SUM(db.discount_amount) * 100.0 / o.subtotal AS DECIMAL(5,2)) as discount_percentage
FROM Orders o
LEFT JOIN Discount_Breakdown db ON o.order_id = db.order_id
WHERE o.order_id = ?
GROUP BY o.order_id;
```

### Revenue Report with Delivery Fees
```sql
SELECT 
    DATE(o.order_time) as order_date,
    COUNT(*) as total_orders,
    SUM(o.subtotal) as subtotal_revenue,
    SUM(o.delivery_fee) as delivery_revenue,    -- NEW
    SUM(o.gst_amount) as gst_revenue,
    SUM(o.tip_amount) as tip_revenue,
    SUM(o.total_amount) as total_revenue
FROM Orders o
WHERE o.delivery_status = 'Completed'
GROUP BY DATE(o.order_time)
ORDER BY order_date DESC;
```

### Student Analytics with Game Rewards
```sql
SELECT 
    s.student_id,
    s.name,
    s.wallet_balance,
    COUNT(DISTINCT o.order_id) as total_orders,
    COUNT(DISTINCT gr.reward_id) as game_rewards,  -- NEW
    COALESCE(SUM(gr.score), 0) as total_game_score,  -- NEW
    AVG(COALESCE(r.rating, 0)) as avg_food_rating,
    COUNT(DISTINCT CASE WHEN r.rider_rating IS NOT NULL THEN 1 END) as delivery_ratings
FROM Students s
LEFT JOIN Orders o ON s.student_id = o.student_id
LEFT JOIN Game_Rewards gr ON s.student_id = gr.student_id  -- NEW
LEFT JOIN Reviews r ON o.order_id = r.order_id
WHERE s.student_id = ?
GROUP BY s.student_id;
```

---

## 🔄 Database Operations

### Add New Discount Breakdown
```python
cursor.execute('''
    INSERT INTO Discount_Breakdown 
    (order_id, discount_type, discount_percentage, discount_amount)
    VALUES (?, ?, ?, ?)
''', (order_id, 'game', 0.10, 150.0))
```

### Award Game Reward
```python
cursor.execute('''
    INSERT INTO Game_Rewards 
    (student_id, order_id, score, discount_percentage)
    VALUES (?, ?, ?, ?)
''', (student_id, order_id, 100, 0.05))
```

### Track Item Combo
```python
cursor.execute('''
    INSERT OR IGNORE INTO AI_Combos 
    (item_1_id, item_2_id, frequency)
    VALUES (?, ?, 1)
    ON CONFLICT(item_1_id, item_2_id) 
    DO UPDATE SET frequency = frequency + 1
''', (item_1, item_2))
```

### Update Order with Delivery Fee
```python
# When creating order
delivery_fee = 200.0 if order_type == 'Delivery' else 0.0
cursor.execute('''
    UPDATE Orders 
    SET delivery_fee = ?, payment_gateway = ?
    WHERE order_id = ?
''', (delivery_fee, 'Stripe', order_id))
```

---

## ⚠️ Important Rules

### 1. Delivery Fee Calculation
- **Rule**: 200 PKR for Delivery, 0 for Pickup
- **When**: Set during order creation based on `order_type`
- **Included in**: Final total amount (subtotal - discounts + gst + delivery_fee + tip)
- **Refundable**: If order canceled, refund = total_amount (excluding delivery_fee)

### 2. Discount Stacking Cap (30%)
- **Rule**: Sum of all discounts ≤ 30% of subtotal
- **When**: Validate when creating/updating order
- **How**: Check `Discount_Breakdown` table before finalizing
- **Violation**: Reject order with error message

### 3. Multi-Stall Order Validation
- **Rule**: Items can be from different stalls
- **Primary Stall**: Set `Orders.stall_id` to first item's stall (for dashboard)
- **Actual Items**: Query `Order_Items` + `Items` to see all stalls
- **Delivery**: All items must ship to same location

### 4. Payment Gateway Mapping
- Cash → COD or Card_on_Delivery
- Campus Wallet → Wallet
- Future: Card → Stripe or Card

### 5. Game Rewards Cap
- **Max Discount**: 25% (capped in data generation)
- **Points Calculation**: 1000 points = 25% discount
- **Per Order**: Can earn 50-500 points

---

## 📈 Performance Tips

### Indexes Available
```sql
-- Created by migration for performance
CREATE INDEX idx_discount_order ON Discount_Breakdown(order_id);
CREATE INDEX idx_game_reward_student ON Game_Rewards(student_id);
CREATE INDEX idx_game_reward_order ON Game_Rewards(order_id);
CREATE INDEX idx_ai_combo_item1 ON AI_Combos(item_1_id);
CREATE INDEX idx_ai_combo_item2 ON AI_Combos(item_2_id);
```

### Query Optimization
- Always filter by `order_id`, `student_id`, or `item_id` when possible
- Use indexes for lookups
- Batch inserts when adding multiple records
- Limit result sets (e.g., LIMIT 5 for recommendations)

---

## 🧪 Testing Queries

### Verify Migration
```sql
-- Check new columns exist
PRAGMA table_info(Orders);  -- Should show delivery_fee, payment_gateway
PRAGMA table_info(Stalls);  -- Should show logo_url, banner_url

-- Check new tables exist
SELECT COUNT(*) FROM Discount_Breakdown;
SELECT COUNT(*) FROM Game_Rewards;
SELECT COUNT(*) FROM AI_Combos;
```

### Sample Data Checks
```sql
-- Verify delivery fees
SELECT COUNT(*), delivery_fee FROM Orders GROUP BY delivery_fee;
-- Expected: ~5,108 orders with 200, ~4,892 with 0

-- Verify payment gateways
SELECT DISTINCT payment_gateway, COUNT(*) FROM Orders GROUP BY payment_gateway;
-- Expected: Wallet, COD, Card_on_Delivery

-- Verify discounts
SELECT COUNT(DISTINCT discount_type) FROM Discount_Breakdown;
-- Expected: 2 (promo, game)

-- Verify game rewards
SELECT COUNT(DISTINCT student_id) FROM Game_Rewards;
-- Expected: ~499 students

-- Verify AI combos
SELECT COUNT(*) FROM AI_Combos WHERE frequency >= 2;
-- Expected: 76 pairs
```

---

## 🚀 Next Steps

1. **Implement Consumer App Backend**
   - Use these queries in your API endpoints
   - Add validation for discount stacking
   - Route payments based on gateway

2. **Update Frontend Components**
   - Display delivery fees in order summary
   - Show discount breakdown on receipt
   - Display game rewards on profile
   - Show "frequently bought together" recommendations
   - Display stall logos and banners

3. **Monitor & Update AI Combos**
   - Add tracking after each real order
   - Update frequency counts
   - Prune old/low-frequency combos

4. **Dashboard Updates**
   - Optional: Display delivery fee revenue
   - Optional: Track payment gateway usage
   - All existing reports still work unchanged

---

## 📞 Support

For issues with:
- **Schema**: Check `CampusEats_Migration_v4.sql`
- **Data Generation**: See `generate_data.py`
- **Verification**: Run `verify_migration.py`
- **Documentation**: See `MIGRATION_v4_COMPLETE.md`

**Last Updated**: 2024-04-25
**Status**: ✅ Production Ready
