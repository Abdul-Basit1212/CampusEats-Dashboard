# Quick Reference Card - CampusEats Schema Migration v3.1

## 🚀 Quick Start

### Fresh Database
```bash
python generate_data.py
```

### Upgrade Existing Database
```bash
python apply_migrations.py
```

---

## 📂 New Files Created

| File | Purpose |
|------|---------|
| `migrations.sql` | SQL statements to apply schema changes |
| `apply_migrations.py` | Safe migration runner for existing DB |
| `MIGRATION_GUIDE.md` | Detailed migration documentation |
| `COMPATIBILITY_VERIFICATION.md` | Backward compatibility analysis |
| `SCHEMA_MIGRATION_SUMMARY.md` | Complete overview |

## 📋 Modified Files

| File | Changes |
|------|---------|
| `CampusEatsDBSchema.sql` | Added 3 new columns, 1 new table, 2 indexes |
| `generate_data.py` | Populates new fields with realistic data |

## ✅ Not Changed

| File | Status |
|------|--------|
| `database.py` | ✓ No changes needed |
| `pages/*.py` | ✓ No changes needed |
| `Home.py` | ✓ No changes needed |

---

## 🎯 What Changed

### Stalls Table
- ✅ Added `avg_prep_time_minutes` (DEFAULT 15)

### Reviews Table
- ✅ Added `rider_rating` (nullable, 1-5)
- ✅ Added `rider_comment` (nullable)

### New Table
- ✅ Created `Order_Status_Logs` (granular status tracking)
- ✅ Added indexes on (order_id, timestamp)

### Preserved
- ✅ `Orders.delivery_status` (dashboard compatibility)
- ✅ All existing data

---

## 🔍 Quick Verification

Check if migrations applied:
```bash
sqlite3 CampusEats.db "SELECT COUNT(*) FROM Order_Status_Logs;"
```

---

## 📊 Data Generated

- **Stalls:** 100 stalls with avg_prep_time 10-30 min
- **Reviews:** ~70% of orders + 50% rider ratings
- **Order_Status_Logs:** ~10K-11K status logs from 10K orders

---

## 🎓 Key Points

1. **Zero Breaking Changes** - Dashboard works unchanged
2. **Safe Migration** - Includes error handling & verification
3. **Complete Tracking** - Order_Status_Logs provides full history
4. **Performance** - New indexes prevent slowdown
5. **Documentation** - Comprehensive guides provided

---

## ⚡ Common Tasks

### Check stall prep times
```sql
SELECT name, avg_prep_time_minutes FROM Stalls LIMIT 5;
```

### View order status history
```sql
SELECT * FROM Order_Status_Logs 
WHERE order_id = 1 ORDER BY timestamp ASC;
```

### Get rider ratings (new feature)
```sql
SELECT AVG(rider_rating) FROM Reviews 
WHERE rider_rating IS NOT NULL;
```

### Verify dashboard still works
```sql
SELECT delivery_status, COUNT(*) FROM Orders 
GROUP BY delivery_status;
```

---

## 📞 Troubleshooting

**Dashboard shows errors?**
→ Run `python apply_migrations.py` to verify

**New columns not appearing?**
→ Check `PRAGMA table_info(Stalls|Reviews)`

**Need to revert?**
→ Restore from database backup before running migrations

---

## 🔗 Full Documentation

- [Migration Guide](MIGRATION_GUIDE.md) - Comprehensive details
- [Compatibility Verification](COMPATIBILITY_VERIFICATION.md) - Query examples
- [Schema Summary](SCHEMA_MIGRATION_SUMMARY.md) - Complete overview

---

**Version:** 3.1  
**Status:** Production Ready ✅  
**Backward Compatible:** 100% ✅
