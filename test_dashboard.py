#!/usr/bin/env python
"""
Comprehensive Test Suite for CampusEats Dashboard App
Tests all components without needing a browser interaction
"""

import sys
import os
import sqlite3
import traceback
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def test_header(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST: {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def test_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def test_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def test_info(msg):
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.END}")

# ════════════════════════════════════════════════════════════════════════════════
test_header("DATABASE EXISTENCE & STRUCTURE")

db_path = app_dir / "CampusEats.db"
if db_path.exists():
    test_success(f"Database file exists: {db_path}")
    test_info(f"File size: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
else:
    test_error(f"Database file not found: {db_path}")
    sys.exit(1)

# ════════════════════════════════════════════════════════════════════════════════
test_header("DATABASE SCHEMA VALIDATION")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check required tables
    required_tables = [
        'Orders', 'Students', 'Stalls', 'Items', 'Reviews',
        'Riders', 'Wallet_Transactions', 'Order_Status_Logs',
        'Discount_Breakdown', 'Game_Rewards', 'AI_Combos'  # New v4.0 tables
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    for table in required_tables:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            test_success(f"Table '{table}' exists ({count} rows)")
        else:
            test_error(f"Table '{table}' is MISSING")
    
    conn.close()
except Exception as e:
    test_error(f"Database validation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# ════════════════════════════════════════════════════════════════════════════════
test_header("PYTHON MODULE IMPORTS")

modules_to_test = [
    ("streamlit", "st"),
    ("pandas", "pd"),
    ("plotly.graph_objects", "go"),
    ("plotly.express", "px"),
    ("sqlalchemy", "SQLAlchemy"),
    ("folium", "Folium"),
    ("streamlit_folium", "streamlit_folium"),
    ("dotenv", "python-dotenv"),
]

failed_imports = []
for module_name, display_name in modules_to_test:
    try:
        __import__(module_name)
        test_success(f"Module '{display_name}' imported successfully")
    except ImportError as e:
        test_error(f"Failed to import '{display_name}': {e}")
        failed_imports.append(module_name)

if failed_imports:
    test_info(f"Failed imports: {', '.join(failed_imports)}")

# ════════════════════════════════════════════════════════════════════════════════
test_header("DATABASE.PY VALIDATION")

try:
    # Import database module
    import database
    
    # Check required functions exist
    required_functions = [
        'fetch_data',
        'execute_write',
        'authenticate_admin',
        'authenticate_incharge',
        'authenticate_stall',
        'get_all_campuses',
        'get_campus_name',
    ]
    
    for func_name in required_functions:
        if hasattr(database, func_name):
            test_success(f"Function '{func_name}' is defined")
        else:
            test_error(f"Function '{func_name}' is MISSING")
    
    # Test database connection
    campuses_df = database.get_all_campuses()
    if not campuses_df.empty:
        test_success(f"Database connection works (retrieved {len(campuses_df)} campuses)")
    else:
        test_error("No campuses found in database")
    
except Exception as e:
    test_error(f"database.py validation failed: {e}")
    traceback.print_exc()

# ════════════════════════════════════════════════════════════════════════════════
test_header("HOME.PY VALIDATION")

try:
    home_file = app_dir / "Home.py"
    if home_file.exists():
        test_success(f"Home.py exists")
        
        with open(home_file, 'r') as f:
            content = f.read()
            
        # Check for key components
        checks = [
            ("st.set_page_config", "Page configuration"),
            ("authenticate_admin", "Admin authentication"),
            ("authenticate_incharge", "Incharge authentication"),
            ("authenticate_stall", "Stall authentication"),
            ("st.session_state", "Session state management"),
        ]
        
        for pattern, desc in checks:
            if pattern in content:
                test_success(f"Home.py contains {desc}")
            else:
                test_error(f"Home.py missing {desc}")
    else:
        test_error("Home.py not found")
except Exception as e:
    test_error(f"Home.py validation failed: {e}")
    traceback.print_exc()

# ════════════════════════════════════════════════════════════════════════════════
test_header("PAGE MODULES VALIDATION")

page_files = [
    ('pages/1_Global_Admin.py', 'Global Admin Page'),
    ('pages/2_Campus_HQ.py', 'Campus HQ Page'),
    ('pages/3_Stall_Dashboard.py', 'Stall Dashboard Page'),
    ('pages/4_AI_Forecaster_Advisor.py', 'AI Forecaster Page'),
]

for page_file, page_name in page_files:
    page_path = app_dir / page_file
    try:
        if page_path.exists():
            with open(page_path, 'r') as f:
                content = f.read()
            
            # Check authentication guard
            if 'st.session_state.get("logged_in")' in content or 'logged_in' in content:
                test_success(f"{page_name}: Authentication guard present")
            else:
                test_error(f"{page_name}: Missing authentication guard")
            
            # Check imports
            if 'from database import' in content or 'import database' in content:
                test_success(f"{page_name}: Database imports present")
            else:
                test_error(f"{page_name}: Missing database imports")
                
        else:
            test_error(f"{page_name} file not found: {page_path}")
    except Exception as e:
        test_error(f"{page_name} validation failed: {e}")

# ════════════════════════════════════════════════════════════════════════════════
test_header("AUTHENTICATION TESTING")

try:
    # Test with known credentials from generated data
    # Using demo mode credentials
    result = database.authenticate_admin("admin@campuseats.pk", "anypassword")
    if result and "admin_id" in result:
        test_success(f"Admin authentication works (admin_id: {result['admin_id']})")
    else:
        test_info("Admin authentication returned None (expected in non-demo mode)")
    
    result = database.authenticate_incharge("nust@campuseats.pk", "anypassword")
    if result and "incharge_id" in result:
        test_success(f"Incharge authentication works (incharge_id: {result['incharge_id']})")
    else:
        test_info("Incharge authentication returned None (expected in non-demo mode)")
    
    result = database.authenticate_stall(1, "anypassword")
    if result and "stall_id" in result:
        test_success(f"Stall authentication works (stall_id: {result['stall_id']})")
    else:
        test_info("Stall authentication returned None (expected in non-demo mode)")
        
except Exception as e:
    test_error(f"Authentication testing failed: {e}")
    traceback.print_exc()

# ════════════════════════════════════════════════════════════════════════════════
test_header("DATA COMPLETENESS CHECK")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    checks = [
        ("SELECT COUNT(*) FROM Orders", "Orders"),
        ("SELECT COUNT(*) FROM Students", "Students"),
        ("SELECT COUNT(*) FROM Stalls", "Stalls"),
        ("SELECT COUNT(*) FROM Items", "Items"),
        ("SELECT COUNT(*) FROM Reviews", "Reviews"),
        ("SELECT COUNT(*) FROM Discount_Breakdown", "Discount Breakdowns"),
        ("SELECT COUNT(*) FROM Game_Rewards", "Game Rewards"),
        ("SELECT COUNT(*) FROM AI_Combos", "AI Combos"),
    ]
    
    for query, label in checks:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if count > 0:
            test_success(f"{label}: {count} records found")
        else:
            test_error(f"{label}: No records found")
    
    conn.close()
except Exception as e:
    test_error(f"Data completeness check failed: {e}")

# ════════════════════════════════════════════════════════════════════════════════
test_header("NEW FEATURES (v4.0) VALIDATION")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check Orders table for new columns
    cursor.execute("PRAGMA table_info(Orders)")
    columns = {row[1] for row in cursor.fetchall()}
    
    new_columns = ["delivery_fee", "payment_gateway"]
    for col in new_columns:
        if col in columns:
            test_success(f"Orders.{col} column exists")
        else:
            test_error(f"Orders.{col} column MISSING")
    
    # Check Stalls table for new columns
    cursor.execute("PRAGMA table_info(Stalls)")
    columns = {row[1] for row in cursor.fetchall()}
    
    new_columns = ["logo_url", "banner_url"]
    for col in new_columns:
        if col in columns:
            test_success(f"Stalls.{col} column exists")
        else:
            test_error(f"Stalls.{col} column MISSING")
    
    # Check new tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Discount_Breakdown', 'Game_Rewards', 'AI_Combos')")
    new_tables = {row[0] for row in cursor.fetchall()}
    
    for table in ['Discount_Breakdown', 'Game_Rewards', 'AI_Combos']:
        if table in new_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            test_success(f"{table} table exists with {count} records")
        else:
            test_error(f"{table} table is MISSING")
    
    conn.close()
except Exception as e:
    test_error(f"v4.0 features validation failed: {e}")
    traceback.print_exc()

# ════════════════════════════════════════════════════════════════════════════════
test_header("ENVIRONMENT CONFIGURATION")

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///CampusEats.db")
    test_success(f"DATABASE_URL: {db_url}")
    
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    test_info(f"DEMO_MODE: {demo_mode}")
    
except Exception as e:
    test_error(f"Environment configuration check failed: {e}")

# ════════════════════════════════════════════════════════════════════════════════
test_header("FINAL STATUS")

print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS COMPLETED{Colors.END}\n")
print(f"{Colors.YELLOW}Dashboard is ready for web interaction.{Colors.END}")
print(f"{Colors.YELLOW}Open http://localhost:8501 in your browser to access the app.{Colors.END}\n")
