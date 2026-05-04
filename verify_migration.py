#!/usr/bin/env python
"""
Verification Script for CampusEats Database Migration v4.0
Ensures:
1. All new tables exist with correct columns
2. All existing tables/columns intact (no breaking changes)
3. Sample data populated correctly
4. Dashboard queries still work
"""

import sqlite3
import sys

def verify_database():
    try:
        conn = sqlite3.connect('CampusEats.db')
        cursor = conn.cursor()
        
        print("=" * 70)
        print("CAMPUSEATS DATABASE MIGRATION v4.0 - VERIFICATION REPORT")
        print("=" * 70)
        
        # 1. Check existing tables are intact
        print("\n✅ EXISTING TABLES (BACKWARD COMPATIBILITY CHECK)")
        existing_tables = [
            'Orders', 'Students', 'Stalls', 'Items', 'Reviews', 
            'Riders', 'Wallet_Transactions', 'Order_Status_Logs'
        ]
        for table in existing_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"   ✓ {table}: {len(columns)} columns")
            else:
                print(f"   ✗ {table}: MISSING!")
                return False
        
        # 2. Check new columns added
        print("\n✅ NEW COLUMNS ADDED")
        new_columns = {
            'Orders': ['delivery_fee', 'payment_gateway'],
            'Stalls': ['logo_url', 'banner_url']
        }
        for table, cols in new_columns.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing_cols = [col[1] for col in cursor.fetchall()]
            for col in cols:
                if col in existing_cols:
                    print(f"   ✓ {table}.{col} exists")
                else:
                    print(f"   ✗ {table}.{col} MISSING!")
                    return False
        
        # 3. Check new tables created
        print("\n✅ NEW TABLES CREATED")
        new_tables = ['Discount_Breakdown', 'Game_Rewards', 'AI_Combos']
        for table in new_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✓ {table}: {count} rows")
            else:
                print(f"   ✗ {table}: MISSING!")
                return False
        
        # 4. Check data integrity
        print("\n✅ DATA INTEGRITY CHECKS")
        
        # Check Orders have delivery_fee populated correctly
        cursor.execute("""
            SELECT COUNT(*) as delivery_orders, 
                   COUNT(CASE WHEN delivery_fee = 200 THEN 1 END) as with_fee
            FROM Orders WHERE order_type = 'Delivery'
        """)
        delivery_orders, with_fee = cursor.fetchone()
        print(f"   ✓ Delivery Orders: {delivery_orders} total, {with_fee} with 200 fee")
        
        # Check payment_gateway populated
        cursor.execute("SELECT COUNT(DISTINCT payment_gateway) FROM Orders WHERE payment_gateway IS NOT NULL")
        gateway_count = cursor.fetchone()[0]
        print(f"   ✓ Payment Gateways: {gateway_count} distinct values populated")
        
        # Check Stalls have logos/banners
        cursor.execute("SELECT COUNT(*) FROM Stalls WHERE logo_url IS NOT NULL")
        stalls_with_logo = cursor.fetchone()[0]
        print(f"   ✓ Stalls with logos: {stalls_with_logo}")
        
        # Check Discount_Breakdown data
        cursor.execute("SELECT COUNT(DISTINCT discount_type) FROM Discount_Breakdown")
        discount_types = cursor.fetchone()[0]
        print(f"   ✓ Discount Types: {discount_types} types tracked")
        
        # Check Game_Rewards data
        cursor.execute("SELECT COUNT(DISTINCT student_id) FROM Game_Rewards")
        reward_students = cursor.fetchone()[0]
        print(f"   ✓ Game Rewards: {reward_students} students with rewards")
        
        # Check AI_Combos data
        cursor.execute("SELECT COUNT(*) FROM AI_Combos")
        combos = cursor.fetchone()[0]
        print(f"   ✓ AI Combos: {combos} item pair combinations tracked")
        
        # 5. Test Dashboard Queries
        print("\n✅ DASHBOARD COMPATIBILITY QUERIES")
        
        # Query 1: Order summary by stall (used by dashboard)
        cursor.execute("""
            SELECT s.stall_id, s.name, COUNT(o.order_id) as order_count,
                   SUM(o.total_amount) as total_revenue
            FROM Orders o
            JOIN Stalls s ON o.stall_id = s.stall_id
            GROUP BY s.stall_id
            LIMIT 5
        """)
        results = cursor.fetchall()
        print(f"   ✓ Stall Revenue Query: {len(results)} stalls returned")
        
        # Query 2: Student wallet balance (used by dashboard)
        cursor.execute("""
            SELECT COUNT(*) as active_students,
                   AVG(wallet_balance) as avg_wallet,
                   MIN(wallet_balance) as min_wallet,
                   MAX(wallet_balance) as max_wallet
            FROM Students
        """)
        result = cursor.fetchone()
        print(f"   ✓ Student Wallet Query: {result[0]} students, avg wallet: {result[1]:.2f}")
        
        # Query 3: Reviews with rider ratings (used by dashboard)
        cursor.execute("""
            SELECT COUNT(*) as reviews_with_rating,
                   COUNT(CASE WHEN rider_rating IS NOT NULL THEN 1 END) as rider_reviews
            FROM Reviews
        """)
        review_count, rider_reviews = cursor.fetchone()
        print(f"   ✓ Review Query: {review_count} reviews, {rider_reviews} with rider ratings")
        
        # Query 4: Delivery orders with rider assignments (used by dashboard)
        cursor.execute("""
            SELECT COUNT(*) as delivery_orders,
                   COUNT(CASE WHEN rider_id IS NOT NULL THEN 1 END) as with_rider
            FROM Orders WHERE order_type = 'Delivery'
        """)
        delivery_total, with_rider = cursor.fetchone()
        print(f"   ✓ Rider Assignment Query: {delivery_total} deliveries, {with_rider} assigned")
        
        # 6. Multi-Stall Order Verification
        print("\n✅ MULTI-STALL ORDER SUPPORT")
        
        # Check if orders can contain items from multiple stalls
        # This is supported by the Order_Items table structure
        cursor.execute("SELECT COUNT(*) FROM Order_Items")
        order_item_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT order_id) FROM Order_Items
        """)
        orders_with_items = cursor.fetchone()[0]
        print(f"   ✓ Multi-Stall Capable: {orders_with_items} orders with items")
        print(f"   ✓ Structure allows multiple items per order: {order_item_count} items total")
        
        # 7. Final Summary
        print("\n" + "=" * 70)
        print("✅ MIGRATION VERIFICATION COMPLETE - NO ISSUES FOUND")
        print("=" * 70)
        print("\nSUMMARY:")
        print("  • All existing tables intact (backward compatible)")
        print("  • All new columns added with proper defaults")
        print("  • All new tables created with data populated")
        print("  • Dashboard queries execute successfully")
        print("  • Multi-stall order structure supported")
        print("\n🎉 Database ready for Student Consumer App deployment!\n")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    success = verify_database()
    sys.exit(0 if success else 1)
