"""
apply_migrations.py — CampusEats Database Migration Runner

This script applies pending migrations to an existing CampusEats.db database.
It reads migrations from migrations.sql and applies them safely.

Usage:
    python apply_migrations.py
"""

import sqlite3
import os
from datetime import datetime

def apply_migrations(db_path='CampusEats.db'):
    """
    Apply migrations from migrations.sql to the database.
    """
    if not os.path.exists(db_path):
        print(f"❌ Error: {db_path} not found. Please ensure the database exists.")
        return False
    
    if not os.path.exists('migrations.sql'):
        print("❌ Error: migrations.sql not found. Please ensure the migrations file exists.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute('PRAGMA foreign_keys = ON')
        
        print(f"🔄 Reading migrations from migrations.sql...")
        with open('migrations.sql', 'r') as f:
            migrations_sql = f.read()
        
        # Split by statements and filter out comments and empty lines
        statements = []
        current_statement = ""
        for line in migrations_sql.split('\n'):
            # Skip comments and empty lines
            if line.strip().startswith('--') or not line.strip():
                continue
            current_statement += line + "\n"
            if line.strip().endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        if not statements:
            print("⚠️  No migration statements found.")
            conn.close()
            return False
        
        print(f"📋 Found {len(statements)} migration statements to apply.\n")
        
        # Apply each migration
        for i, statement in enumerate(statements, 1):
            try:
                print(f"[{i}/{len(statements)}] Applying migration...")
                print(f"   SQL: {statement[:60]}..." if len(statement) > 60 else f"   SQL: {statement}")
                cursor.execute(statement)
                print(f"   ✅ Success\n")
            except sqlite3.OperationalError as e:
                # Check if it's a "column already exists" error (migration already applied)
                if "already exists" in str(e) or "duplicate column" in str(e):
                    print(f"   ⚠️  Already applied (skipping): {e}\n")
                else:
                    print(f"   ❌ Error: {e}\n")
                    conn.rollback()
                    conn.close()
                    return False
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}\n")
                conn.rollback()
                conn.close()
                return False
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("=" * 60)
        print("✅ All migrations applied successfully!")
        print("=" * 60)
        print("\n📊 Schema changes:")
        print("   • Added avg_prep_time_minutes to Stalls (default: 15 min)")
        print("   • Added rider_rating & rider_comment to Reviews")
        print("   • Created Order_Status_Logs table for granular tracking")
        print("   • Existing Orders data preserved for dashboard compatibility")
        print("\n💡 Note: The delivery_status column remains in Orders for")
        print("   backward compatibility with the Streamlit dashboard.")
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return False

def verify_schema(db_path='CampusEats.db'):
    """
    Verify that migrations were applied correctly.
    """
    print("\n🔍 Verifying schema changes...\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check Stalls table
        cursor.execute("PRAGMA table_info(Stalls)")
        stalls_columns = {row[1] for row in cursor.fetchall()}
        if 'avg_prep_time_minutes' in stalls_columns:
            print("✅ Stalls.avg_prep_time_minutes: OK")
        else:
            print("❌ Stalls.avg_prep_time_minutes: MISSING")
        
        # Check Reviews table
        cursor.execute("PRAGMA table_info(Reviews)")
        reviews_columns = {row[1] for row in cursor.fetchall()}
        if 'rider_rating' in reviews_columns and 'rider_comment' in reviews_columns:
            print("✅ Reviews.rider_rating & rider_comment: OK")
        else:
            print("❌ Reviews.rider_rating or rider_comment: MISSING")
        
        # Check Order_Status_Logs table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Order_Status_Logs'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM Order_Status_Logs")
            count = cursor.fetchone()[0]
            print(f"✅ Order_Status_Logs table: OK ({count} records)")
        else:
            print("❌ Order_Status_Logs table: MISSING")
        
        # Verify Orders table still has delivery_status (backward compatibility)
        cursor.execute("PRAGMA table_info(Orders)")
        orders_columns = {row[1] for row in cursor.fetchall()}
        if 'delivery_status' in orders_columns:
            print("✅ Orders.delivery_status: OK (backward compatibility preserved)")
        else:
            print("❌ Orders.delivery_status: MISSING (critical!)")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Schema verification complete!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("CampusEats Database Migration Runner v3.1")
    print("=" * 60)
    print()
    
    success = apply_migrations()
    if success:
        verify_schema()
    else:
        print("\n❌ Migration failed. Please check the errors above.")
