# CampusEats Database Schema v3.1 - Migration Guide

## Overview

This document describes the database schema migrations for CampusEats v3.1, which adds new features while maintaining **100% backward compatibility** with the existing Streamlit dashboard.

## What's New

### 1. **Stalls Table - Average Preparation Time**

**Column Added:** `avg_prep_time_minutes` (INTEGER, DEFAULT 15)

- **Purpose:** Track average food preparation time per stall
- **Default:** 15 minutes for existing stalls
- **Impact:** Dashboard queries unaffected (default value ensures no NULL issues)
- **Use Case:** Future consumer app can show estimated wait times

```sql
ALTER TABLE Stalls ADD COLUMN avg_prep_time_minutes INTEGER DEFAULT 15;
```

**Example Query:**
```sql
SELECT name, avg_prep_time_minutes 
FROM Stalls 
WHERE stall_id = 5;
```

---

### 2. **Reviews Table - Rider Experience Ratings**

**Columns Added:**
- `rider_rating` (INTEGER, CHECK(1-5), NULLABLE)
- `rider_comment` (TEXT, NULLABLE)

- **Purpose:** Separate delivery experience feedback from food quality
- **Default:** NULL (only populated for delivery orders if customer provides feedback)
- **Impact:** No NULL issues in dashboard (columns are truly optional)
- **Use Case:** Track rider performance, improve delivery service

```sql
ALTER TABLE Reviews ADD COLUMN rider_rating INTEGER CHECK(rider_rating >= 1 AND rider_rating <= 5) DEFAULT NULL;
ALTER TABLE Reviews ADD COLUMN rider_comment TEXT DEFAULT NULL;
```

**Example Query:**
```sql
SELECT 
    r.review_id,
    r.rating AS food_rating,
    r.rider_rating,
    r.comment AS food_comment,
    r.rider_comment
FROM Reviews r
WHERE r.rider_rating IS NOT NULL
ORDER BY r.review_time DESC;
```

---

### 3. **Order_Status_Logs Table - Granular Status Tracking**

**New Table Created:**

```sql
CREATE TABLE Order_Status_Logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
);

CREATE INDEX idx_order_status_logs_order ON Order_Status_Logs(order_id);
CREATE INDEX idx_order_status_logs_timestamp ON Order_Status_Logs(timestamp);
```

**Purpose:**
- Track complete status history for each order
- Enable consumer app to show real-time order progress
- Maintain audit trail of all status changes

**Statuses Tracked:**
- `Pending` → `Confirmed` → `Preparing` → `Ready` → `Out for Delivery` → `Completed`
- `Canceled` (with reason notes)

**Example Query:**
```sql
SELECT 
    log_id,
    order_id,
    status,
    timestamp,
    notes
FROM Order_Status_Logs
WHERE order_id = 42
ORDER BY timestamp ASC;
```

---

## Backward Compatibility

### ✅ Dashboard Protected

The existing Streamlit dashboard remains **100% functional** because:

1. **`Orders.delivery_status` preserved** - NOT removed
   - All existing KPI queries continue to work
   - No code changes required in `database.py`

2. **Default values prevent NULLs** - `avg_prep_time_minutes` defaults to 15
   - Existing queries don't break on NULL values
   - Data generator populates new fields automatically

3. **New columns are optional** - `rider_rating` and `rider_comment` are nullable
   - Dashboard never queries these columns
   - No performance impact on existing queries

### 📊 Example Dashboard Query (Unaffected)

```python
# This query still works EXACTLY as before
df = fetch_data("""
    SELECT 
        SUM(total_amount) AS total_revenue,
        COUNT(DISTINCT student_id) AS active_students
    FROM Orders
    WHERE delivery_status = 'Completed'
      AND order_time >= DATE('now', '-30 days')
""")
```

---

## How to Apply Migrations

### Option 1: Fresh Database (Recommended)

```bash
python generate_data.py
```

This creates a new database with all schema changes and populated data.

### Option 2: Upgrade Existing Database

```bash
python apply_migrations.py
```

This applies migrations to an existing `CampusEats.db` file while preserving all data.

### Verification

The script automatically verifies:
- ✅ `avg_prep_time_minutes` added to Stalls
- ✅ `rider_rating` & `rider_comment` added to Reviews
- ✅ `Order_Status_Logs` table created
- ✅ `Orders.delivery_status` still exists (backward compatibility)

---

## Data Generator Updates

### Modified: `generate_data.py`

The data generator now:

1. **Populates `avg_prep_time_minutes`** for each stall (random 10-30 minutes)
   ```python
   avg_prep_time = random.randint(10, 30)
   ```

2. **Creates rider ratings** for 50% of delivery order reviews
   ```python
   if o_type == 'Delivery' and random.random() < 0.5:
       rider_rating = random.randint(1, 5)
       rider_comment = random.choice(rider_comments)
   ```

3. **Generates Order_Status_Logs** for all orders
   ```python
   # Creates initial log on order creation
   # Creates cancellation log if order is canceled
   ```

---

## Migration Files

### Files Modified
- `CampusEatsDBSchema.sql` - Updated schema with new columns and table
- `generate_data.py` - Updated to populate new fields

### Files Created
- `migrations.sql` - SQL migration statements
- `apply_migrations.py` - Migration runner script
- `MIGRATION_GUIDE.md` - This guide

---

## Database Diagram (Simplified)

```
Orders (existing)
  ├─ delivery_status ✓ (preserved for dashboard)
  ├─ order_id (FK to Order_Status_Logs)
  └─ ... other fields

Order_Status_Logs (NEW)
  ├─ log_id (PK)
  ├─ order_id (FK)
  ├─ status (TEXT)
  ├─ timestamp (DATETIME)
  └─ notes (TEXT)

Reviews (updated)
  ├─ review_id (PK)
  ├─ rating (1-5, for food)
  ├─ comment (TEXT)
  ├─ rider_rating (1-5, NEW, NULLABLE)
  ├─ rider_comment (TEXT, NEW, NULLABLE)
  └─ ... other fields

Stalls (updated)
  ├─ stall_id (PK)
  ├─ name, category, owner_name
  ├─ avg_prep_time_minutes (NEW, DEFAULT 15)
  └─ ... other fields
```

---

## Query Examples for New Features

### Get stall prep times for consumer app

```sql
SELECT 
    s.stall_id,
    s.name,
    s.avg_prep_time_minutes,
    ROUND(AVG(sr.rating), 2) AS avg_rating
FROM Stalls s
LEFT JOIN Reviews sr ON sr.order_id IN (
    SELECT order_id FROM Orders WHERE stall_id = s.stall_id
)
WHERE s.is_active = 1
ORDER BY s.avg_prep_time_minutes ASC;
```

### Get rider performance metrics

```sql
SELECT 
    r.rider_id,
    r.name,
    COUNT(DISTINCT rr.review_id) AS review_count,
    ROUND(AVG(CAST(rr.rider_rating AS FLOAT)), 2) AS avg_rating
FROM Riders r
LEFT JOIN Reviews rr ON rr.rider_rating IS NOT NULL
    AND r.rider_id IN (
        SELECT rider_id FROM Orders 
        WHERE order_id = rr.order_id
    )
GROUP BY r.rider_id
ORDER BY avg_rating DESC;
```

### Track order status evolution

```sql
SELECT 
    o.order_id,
    o.student_id,
    osl.status,
    osl.timestamp,
    osl.notes,
    ROUND((julianday(osl.timestamp) - julianday(LAG(osl.timestamp) OVER (
        PARTITION BY o.order_id ORDER BY osl.timestamp
    ))) * 1440, 0) AS minutes_in_status
FROM Orders o
JOIN Order_Status_Logs osl ON o.order_id = osl.order_id
WHERE o.order_id = 42
ORDER BY osl.timestamp ASC;
```

---

## Performance Considerations

✅ **No Performance Impact**

- Indexes added on frequently queried columns:
  - `Order_Status_Logs(order_id)` - Fast lookup of status history
  - `Order_Status_Logs(timestamp)` - Efficient time-based queries

- New columns don't affect existing queries
- Default values prevent table scans for NULL checks

---

## Troubleshooting

### Q: Dashboard shows errors after migration?

**A:** Run verification:
```bash
python apply_migrations.py
```

If `Orders.delivery_status` is missing (should never happen), the migration failed. Restore from backup and retry.

### Q: New rider ratings don't appear in dashboard?

**A:** Expected behavior. Rider ratings are for future consumer app, not the current dashboard. They're stored in `Reviews.rider_rating` which the dashboard doesn't query.

### Q: How do I check if migrations were applied?

**A:** Query the database:
```bash
sqlite3 CampusEats.db "PRAGMA table_info(Order_Status_Logs);"
```

Should show the table structure if migration succeeded.

---

## Future Roadmap

These schema changes enable:

1. ✅ Order status tracking for consumer app
2. ✅ Rider performance metrics
3. ✅ Preparation time estimates
4. ✅ Delivery experience feedback
5. 🔄 Estimated delivery time calculations
6. 🔄 Rider assignment optimization
7. 🔄 Advanced analytics dashboard

---

## Contact & Support

For schema questions or issues:
- Check the `MIGRATION_GUIDE.md`
- Review `apply_migrations.py` for troubleshooting
- Verify with `PRAGMA table_info()` commands

Last Updated: April 2026
Schema Version: 3.1
