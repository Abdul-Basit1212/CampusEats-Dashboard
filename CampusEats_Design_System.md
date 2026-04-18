# CampusEats Design System

This document outlines the comprehensive design system and color palette for CampusEats. The platform consists of two distinct applications—the Student App and the Stall Owner Dashboard—that share a unified brand identity while maintaining UI layouts optimized for their specific tasks.

## 🎨 Shared Color Palette

This palette bridges the gap between the energetic student app and the professional dashboard.

* **Primary Brand (Spicy Orange): `#FF6B35`**
  * *Why:* Orange stimulates appetite, feels youthful, and grabs attention.
  * *Usage:* "Add to Cart" buttons, primary logos, active navigation tabs, and key highlights.

* **Secondary Action (Fresh Green): `#2EC4B6`**
  * *Why:* Green represents freshness, success, and trust.
  * *Usage:* Order success screens, "Predict" buttons, positive financial KPIs, and vegetarian/healthy tags.

* **Accent & Ratings (Warm Yellow): `#FFC857`**
  * *Why:* A friendly, warm color associated with happiness.
  * *Usage:* Star ratings, "Top Seller" badges, and subtle UI accents.

* **Alert & Warning (Tomato Red): `#E71D36`**
  * *Usage:* Canceled orders, negative revenue trends, and error messages.

* **Backgrounds (Soft Off-White): `#FAFAFA`**
  * *Why:* Pure white can cause eye strain. A very soft off-white makes the vibrant orange and green pop without glaring.

* **Typography & Borders (Slate): `#011627`**
  * *Why:* Pure black (`#000000`) is too harsh. Slate provides high contrast for readability while keeping the aesthetic soft.

---

## 📱 App 1: The Student App (Next.js)

**Vibe:** Appetizing, fast, gamified, and effortless.

### Design Principles:
* **Mobile-First Layout:** The entire design should be built for thumbs. Use a persistent bottom navigation bar (Home, Search, Cart, Profile) rather than a desktop-style top menu.
* **Soft Geometry:** Avoid sharp corners. Use rounded corners (`rounded-2xl` in Tailwind) for food images, buttons, and floating cards. This makes the interface feel modern and friendly.
* **Card-Based Interface:** Wrap stalls and menu items in clean, white cards with a very soft drop shadow (`shadow-sm` or `shadow-md`).
* **Visual Hierarchy:** Food photography should take up the most real estate. Keep text concise.
* **Typography:** Use a rounded, friendly sans-serif font like **Poppins** or **Nunito** for headings, and standard **Inter** for readable body text.

---

## 💻 App 2: The Stall Owner Dashboard (Streamlit)

**Vibe:** Professional, clear, reassuring, and data-driven.

### Design Principles:
* **Desktop-First Layout:** Stall owners and admins will likely view this on laptops or tablets. Utilize a persistent left-hand sidebar for navigation between modules.
* **Let the Data Breathe:** Do not overuse the brand colors here. The background should be soft gray (`#FAFAFA`), and the dashboard cards should be crisp white. Reserve the Spicy Orange and Fresh Green strictly for data visualization (Plotly charts) and primary action buttons.
* **High-Density Scannability:** Use clean, structured tables with alternating row colors (zebra striping) for easy reading of dense data like inventory and reviews.
* **Typography:** Use a highly legible, geometric sans-serif font like **Inter** or **Roboto**. These fonts feature monospaced numerals, ensuring that columns of revenue and order numbers line up perfectly and are easy to read at a glance.
