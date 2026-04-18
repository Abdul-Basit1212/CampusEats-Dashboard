import sqlite3
import random
import os
from datetime import datetime, timedelta

def create_and_populate_db():
    if os.path.exists('CampusEats.db'):
        os.remove('CampusEats.db')

    conn = sqlite3.connect('CampusEats.db')
    cursor = conn.cursor()

    # Read schema
    with open('CampusEatsDBSchema.sql', 'r') as f:
        cursor.executescript(f.read())

    def random_date(start_date, end_date):
        time_between = end_date - start_date
        random_number_of_days = random.randrange(max(1, time_between.days))
        return start_date + timedelta(days=random_number_of_days, hours=random.randrange(24), minutes=random.randrange(60))

    # Generate data for last 90 days from today
    end_d = datetime.now()
    start_d = end_d - timedelta(days=90)
    default_hash = "pbkdf2:sha256:mockhashvalue"

    # 1. Platform Settings
    cursor.execute("INSERT INTO Platform_Settings (setting_key, setting_value, description) VALUES ('global_gst', '0.15', 'Global GST applied to all orders')")

    # 2. Campuses, Admins, Incharges
    campuses = [('NUST', 33.6425, 72.9926), ('UET Lahore', 31.5794, 74.3541), ('IBA Karachi', 24.9398, 67.1139)]
    cursor.executemany('INSERT INTO Campuses (name, real_location_lat, real_location_long) VALUES (?, ?, ?)', campuses)
    cursor.execute("INSERT INTO Global_Admins (name, email, password_hash) VALUES ('Super Admin', 'admin@campuseats.pk', ?)", (default_hash,))
    cursor.executemany('INSERT INTO Campus_Incharges (campus_id, name, email, password_hash) VALUES (?, ?, ?, ?)', [
        (1, 'NUST Manager', 'nust@campuseats.pk', default_hash), (2, 'UET Manager', 'uet@campuseats.pk', default_hash), (3, 'IBA Manager', 'iba@campuseats.pk', default_hash)
    ])

    # 3. Promotions
    promos = [('WELCOME10', 0.10, 100), ('MIDTERMS20', 0.20, 200), ('GAMEDAY50', 0.50, 300)]
    cursor.executemany('INSERT INTO Promotions (promo_code, discount_percentage, max_discount_amount) VALUES (?, ?, ?)', promos)

    # 4. Riders (30 Riders per campus with random locations around campus)
    riders = []
    rider_names = ['Zeeshan', 'Kamran', 'Tariq', 'Farhan', 'Shoaib', 'Faisal', 'Naveed', 'Waqas', 'Adnan', 'Imran']
    for c_id in range(1, 4):
        campus_lat, campus_lon = campuses[c_id-1][1], campuses[c_id-1][2]
        for _ in range(30):
            r_name = f"{random.choice(rider_names)} {random.randint(1,99)}"
            # Spread riders around campus center by ±0.01 degrees (~1km)
            rider_lat = campus_lat + random.uniform(-0.01, 0.01)
            rider_lon = campus_lon + random.uniform(-0.01, 0.01)
            riders.append((c_id, r_name, f"03{random.randint(10000000, 49999999)}", 'Available', rider_lat, rider_lon))
    cursor.executemany('INSERT INTO Riders (campus_id, name, phone_number, current_status, location_lat, location_long) VALUES (?, ?, ?, ?, ?, ?)', riders)

    # Organized Riders by Campus for Orders
    cursor.execute('SELECT rider_id, campus_id FROM Riders')
    riders_by_campus = {1: [], 2: [], 3: []}
    for r_id, c_id in cursor.fetchall():
        riders_by_campus[c_id].append(r_id)

    # 5. Students & Initial Wallet Ledger
    students = []
    wallet_ledgers = []
    student_names = ['Ali', 'Omar', 'Hamza', 'Hassan', 'Zain', 'Bilal', 'Fatima', 'Ayesha', 'Sana', 'Iqra']
    for s_id in range(1, 1001):
        c_id = random.randint(1, 3)
        name = f"{random.choice(student_names)} {s_id}"
        email = f"student{s_id}@student.edu.pk"
        wallet = random.uniform(2000.0, 15000.0)
        j_date = random_date(start_d, end_d).strftime('%Y-%m-%d %H:%M:%S')
        students.append((c_id, name, email, default_hash, wallet, j_date))
        wallet_ledgers.append((s_id, wallet, 'Top-up', j_date))
        
    cursor.executemany('INSERT INTO Students (campus_id, name, email, password_hash, wallet_balance, join_date) VALUES (?, ?, ?, ?, ?, ?)', students)
    cursor.executemany('INSERT INTO Wallet_Transactions (student_id, amount, transaction_type, timestamp) VALUES (?, ?, ?, ?)', wallet_ledgers)

    # 6. Stalls & Items with CONSTANT stalls per campus
    # Stalls 1-33 → campus 1, 34-66 → campus 2, 67-100 → campus 3
    stalls = []
    for st_id in range(1, 101):
        if st_id <= 33:
            c_id = 1
        elif st_id <= 66:
            c_id = 2
        else:
            c_id = 3
        
        campus_lat, campus_lon = campuses[c_id-1][1], campuses[c_id-1][2]
        stall_lat = campus_lat + random.uniform(-0.015, 0.015)
        stall_lon = campus_lon + random.uniform(-0.015, 0.015)
        stalls.append((c_id, f"Stall {st_id}", random.choice(['Desi', 'Fast Food', 'Snacks']), 'Owner', default_hash, stall_lat, stall_lon, 1))
    cursor.executemany('INSERT INTO Stalls (campus_id, name, category, owner_name, password_hash, location_lat, location_long, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', stalls)

    # Item categories with realistic items
    item_categories = {
        'Biryani': ['Chicken Biryani', 'Mutton Biryani', 'Vegetable Biryani', 'Prawn Biryani', 'Mixed Biryani'],
        'Karahi': ['Chicken Karahi', 'Mutton Karahi', 'Shrimp Karahi', 'Mixed Karahi', 'Vegetable Karahi'],
        'BBQ': ['Seekh Kabab', 'Shami Kabab', 'Tikka', 'Tandoori Chicken', 'Grilled Fish'],
        'Burgers': ['Beef Burger', 'Chicken Burger', 'Veggie Burger', 'Double Cheese Burger', 'Fries Combo'],
        'Pizza': ['Margherita', 'Pepperoni', 'BBQ Chicken', 'Vegetarian', 'Meat Lovers'],
        'Desserts': ['Brownies', 'Cheesecake', 'Ice Cream', 'Kheer', 'Gulab Jaman'],
        'Beverages': ['Mango Lassi', 'Cold Coffee', 'Iced Tea', 'Fresh Juice', 'Smoothie']
    }
    
    items = []
    for st_id in range(1, 101):
        # Each stall gets items from 2-3 categories
        selected_categories = random.sample(list(item_categories.keys()), random.randint(2, 3))
        item_index = 0
        for category in selected_categories:
            for item_name in item_categories[category]:
                cost = random.randint(50, 300)
                items.append((st_id, item_name, category, cost + random.randint(30, 80), cost, None, 1))
                item_index += 1
                if item_index >= 6:  # Limit items per stall
                    break
            if item_index >= 6:
                break
    cursor.executemany('INSERT INTO Items (stall_id, name, category, selling_price, cost_price, image_url, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)', items)

    cursor.execute('SELECT item_id, stall_id, selling_price FROM Items')
    items_by_stall = {}
    for i_id, s_id, price in cursor.fetchall():
        items_by_stall.setdefault(s_id, []).append((i_id, price))

    # 7. Orders & deductions
    orders = []
    order_items = []
    new_wallet_ledgers = []
    
    for o_id in range(1, 10001):
        s_id = random.randint(1, 1000)
        cursor.execute('SELECT campus_id FROM Students WHERE student_id = ?', (s_id,))
        c_id = cursor.fetchone()[0]
        
        cursor.execute('SELECT stall_id FROM Stalls WHERE campus_id = ?', (c_id,))
        valid_stalls = [row[0] for row in cursor.fetchall()]
        st_id = random.choice(valid_stalls)
        
        o_time = random_date(start_d, end_d).strftime('%Y-%m-%d %H:%M:%S')
        o_type = random.choice(['Pickup', 'Delivery'])
        r_id = random.choice(riders_by_campus[c_id]) if o_type == 'Delivery' else None
        
        pm = random.choice(['Cash', 'Campus Wallet'])
        status = 'Completed' if random.random() < 0.85 else 'Canceled'
        
        subtotal = 0.0
        selected_items = []
        for i_id, price in random.sample(items_by_stall[st_id], 2):
            order_items.append((o_id, i_id, 1, price))
            selected_items.append(i_id)
            subtotal += price
            
        promo = random.choice([None, 'WELCOME10', 'MIDTERMS20'])
        d_amt = 0.0
        if promo:
            pct, cap = next((p[1], p[2]) for p in promos if p[0] == promo)
            d_amt = min(subtotal * pct, cap)
            
        gst = (subtotal - d_amt) * 0.15
        
        # Add tip for 60% of completed delivery orders
        tip = 0.0
        if status == 'Completed' and o_type == 'Delivery' and random.random() < 0.6:
            tip = random.choice([50, 75, 100, 150, 200])
        
        total = (subtotal - d_amt) + gst + tip
        
        # Add cancel reason if order is canceled
        cancel_reason = None
        if status == 'Canceled':
            cancel_reason = random.choice(['Out of Stock', 'Payment Failed', 'Rider Unavailable', 'Customer Request', 'System Error'])
        
        orders.append((s_id, st_id, r_id, o_time, o_type, subtotal, promo, d_amt, gst, tip, total, pm, 'Paid', status, cancel_reason))
        
        if pm == 'Campus Wallet' and status == 'Completed':
            new_wallet_ledgers.append((s_id, -total, 'Order Payment', o_time))

    cursor.executemany('''
        INSERT INTO Orders 
        (student_id, stall_id, rider_id, order_time, order_type, subtotal, promo_code, discount_amount, gst_amount, tip_amount, total_amount, payment_method, payment_status, delivery_status, cancel_reason) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', orders)
    cursor.executemany('INSERT INTO Order_Items (order_id, item_id, quantity, unit_price) VALUES (?, ?, ?, ?)', order_items)
    cursor.executemany('INSERT INTO Wallet_Transactions (student_id, amount, transaction_type, timestamp) VALUES (?, ?, ?, ?)', new_wallet_ledgers)
    
    # 8. Reviews & Ratings for completed orders (70% of completed orders get reviews)
    cursor.execute('SELECT order_id, stall_id FROM Orders WHERE delivery_status = "Completed"')
    completed_orders = cursor.fetchall()
    
    reviews = []
    review_comments = [
        "Great food and fast delivery!",
        "Delicious! Will order again.",
        "Good quality, could be fresher.",
        "Amazing taste, highly recommend!",
        "Average, but decent portion size.",
        "Excellent service and food.",
        "Fresh ingredients, very satisfied.",
        "Quick delivery, hot food.",
        "Not as expected, but acceptable.",
        "Perfect! Exactly what I wanted.",
        "Tasty biryani, 10/10!",
        "Good value for money.",
        "Packaging could be better.",
        "Loved the flavors!",
        "Worth the price."
    ]
    
    for o_id, st_id in completed_orders:
        if random.random() < 0.7:  # 70% of completed orders get reviews
            # Order-level review distribution: 10% 1-2, 20% 3, 70% 4-5 (avg ~4.1)
            rand = random.random()
            if rand < 0.05:
                rating = 1
            elif rand < 0.1:
                rating = 2
            elif rand < 0.25:
                rating = 3
            elif rand < 0.5:
                rating = 4
            else:
                rating = 5
            comment = random.choice(review_comments)
            review_time = (datetime.strptime(
                cursor.execute('SELECT order_time FROM Orders WHERE order_id = ?', (o_id,)).fetchone()[0],
                '%Y-%m-%d %H:%M:%S'
            ) + timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S')
            reviews.append((o_id, None, rating, comment, review_time))
            
            # Item-level reviews (30% of reviewed orders get item reviews)
            if random.random() < 0.3:
                cursor.execute('SELECT item_id FROM Order_Items WHERE order_id = ?', (o_id,))
                items_in_order = [row[0] for row in cursor.fetchall()]
                for i_id in items_in_order:
                    if random.random() < 0.6:  # 60% of items in reviewed orders get item reviews
                        rand = random.random()
                        if rand < 0.05:
                            item_rating = 1
                        elif rand < 0.1:
                            item_rating = 2
                        elif rand < 0.25:
                            item_rating = 3
                        elif rand < 0.5:
                            item_rating = 4
                        else:
                            item_rating = 5
                        item_comment = random.choice(review_comments)
                        reviews.append((o_id, i_id, item_rating, item_comment, review_time))
    
    cursor.executemany('INSERT INTO Reviews (order_id, item_id, rating, comment, review_time) VALUES (?, ?, ?, ?, ?)', reviews)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_and_populate_db()
