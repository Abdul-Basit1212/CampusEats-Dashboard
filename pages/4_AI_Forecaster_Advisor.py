"""
pages/4_🔮_AI_Forecaster_&_Advisor.py — CampusEats Dashboard
ML-based sales forecaster (RandomForestRegressor) + Gemini AI Business Advisor chatbot.
Access: all authenticated roles (output scoped to role).
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from database import fetch_data, get_all_campuses
from security import validate_session, log_audit
from dotenv import load_dotenv

load_dotenv()

# ── Page config & auth guard ──────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Forecaster · CampusEats", page_icon="🔮", layout="wide"
)

# ⚠️ SECURITY: Validate session on EVERY page load
if not validate_session():
    st.warning("Session expired or invalid. Please login again.")
    st.switch_page("Home.py")
    st.stop()

# ── Brand colours ─────────────────────────────────────────────────────────────
ORANGE = "#FF6B35"
GREEN  = "#2EC4B6"
RED    = "#E71D36"
YELLOW = "#FFC857"

# ── THEME & STYLING ──────────────────────────────────────────────────────────
def get_chart_template():
    """Get chart template based on Streamlit theme."""
    return "plotly_dark" if st.session_state.get("theme", "dark") == "dark" else "plotly"

def styled_chart(fig, template=None):
    """Apply theme styling to Plotly charts."""
    if template is None:
        template = get_chart_template()
    fig.update_layout(
        template=template,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    return fig


def get_advice_box_colors():
    """Get theme-responsive colors for advice boxes."""
    is_dark = st.session_state.get("theme", "dark") == "dark"
    return {
        "bg": "#1a3d3a" if is_dark else "#E8F8F5",
        "border": GREEN,
        "text": "#a0d8d4" if is_dark else "#011627",
    }

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 AI Forecaster Advisor")
    st.divider()
    st.markdown(f"### 👋 {st.session_state.user_name}")
    role_icons = {"admin": "🌍 Global Admin", "incharge": "📍 Campus Incharge", "owner": "🏪 Stall Owner"}
    st.markdown(f"**Role:** {role_icons.get(st.session_state.user_role, '')}")
    st.divider()
    section = st.radio(
        "Navigate",
        ["🔮 Sales Forecaster", "🤖 AI Business Advisor"],
        label_visibility="collapsed",
    )
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("Home.py")

role = st.session_state.user_role
entity_id = st.session_state.entity_id
campus_id = st.session_state.campus_id

# ═══════════════════════════════════════════════════════════════════════════════
# ── DATA FETCHERS ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600, show_spinner=False)
def get_orders_for_ml(scope: str, scope_id: int | None) -> pd.DataFrame:
    """
    Load historical orders for ML training, scoped appropriately.
    scope: 'platform' | 'campus' | 'stall'
    """
    if scope == "stall":
        where = "WHERE o.stall_id = :sid"
        params = {"sid": scope_id}
    elif scope == "campus":
        where = "WHERE st.campus_id = :cid"
        params = {"cid": scope_id}
    else:
        where = ""
        params = {}

    return fetch_data(f"""
        SELECT o.order_id,
               o.order_time,
               o.stall_id,
               st.campus_id,
               st.category,
               o.total_amount,
               o.delivery_status,
               CAST(strftime('%H', o.order_time) AS INTEGER) AS hour,
               CAST(strftime('%w', o.order_time) AS INTEGER) AS dow,
               CAST(strftime('%m', o.order_time) AS INTEGER) AS month
        FROM Orders o
        JOIN Stalls st ON o.stall_id = st.stall_id
        {where}
        ORDER BY o.order_time
    """, params)

@st.cache_data(ttl=300, show_spinner=False)
def get_stall_context_for_ai(stall_id: int) -> pd.DataFrame:
    """Last 14 days of financial context for the Gemini prompt."""
    return fetch_data("""
        SELECT DATE(o.order_time)  AS order_date,
               COUNT(o.order_id)   AS total_orders,
               SUM(o.subtotal)     AS subtotal,
               SUM(o.gst_amount)   AS gst,
               SUM(o.tip_amount)   AS tips,
               SUM(o.total_amount) AS total_revenue,
               SUM(CASE WHEN o.delivery_status='Canceled'
                   THEN 1 ELSE 0 END) AS cancellations,
               COALESCE(AVG(r.rating), 0) AS avg_rating
        FROM Orders o
        LEFT JOIN Reviews r ON o.order_id = r.order_id
        WHERE o.stall_id = :sid
          AND o.order_time >= DATE('now','-14 days')
        GROUP BY DATE(o.order_time)
        ORDER BY order_date
    """, {"sid": stall_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_stall_reviews_for_ai(stall_id: int) -> pd.DataFrame:
    """Last 14 days of reviews and ratings for the stall."""
    return fetch_data("""
        SELECT r.review_id,
               r.rating,
               r.comment,
               r.review_time,
               i.name AS item_name,
               o.order_id,
               COALESCE(i.category, 'General') AS item_category
        FROM Reviews r
        JOIN Orders o ON r.order_id = o.order_id
        LEFT JOIN Items i ON r.item_id = i.item_id
        WHERE o.stall_id = :sid
          AND r.review_time >= DATE('now','-14 days')
        ORDER BY r.review_time DESC
    """, {"sid": stall_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_competitive_stalls_for_ai(stall_id: int) -> dict:
    """Fetch competitor stalls in same campus and category (30-day stats)."""
    # Get current stall's campus and category
    current_stall = fetch_data(
        "SELECT campus_id, category FROM Stalls WHERE stall_id = :sid",
        {"sid": stall_id}
    )
    
    if current_stall.empty:
        return {"competitors_df": pd.DataFrame(), "summary": "No competitor data available"}
    
    campus_id = int(current_stall.iloc[0]["campus_id"])
    category = current_stall.iloc[0]["category"]
    
    # Get competitor stats
    competitors = fetch_data("""
        SELECT st.stall_id,
               st.name AS stall_name,
               COUNT(DISTINCT o.order_id) AS total_orders_30d,
               SUM(CASE WHEN o.delivery_status='Completed' THEN 1 ELSE 0 END) AS completed_orders,
               ROUND(100.0 * SUM(CASE WHEN o.delivery_status='Completed' THEN 1 ELSE 0 END) 
                   / NULLIF(COUNT(DISTINCT o.order_id), 0), 1) AS completion_rate,
               ROUND(AVG(r.rating), 2) AS avg_rating,
               COUNT(DISTINCT r.review_id) AS review_count,
               ROUND(SUM(o.total_amount), 0) AS total_revenue_30d
        FROM Stalls st
        LEFT JOIN Orders o ON st.stall_id = o.stall_id 
                          AND o.order_time >= DATE('now','-14 days')
        LEFT JOIN Reviews r ON o.order_id = r.order_id AND r.item_id IS NULL
        WHERE st.campus_id = :cid
          AND st.category = :cat
          AND st.stall_id != :sid
          AND st.is_active = 1
        GROUP BY st.stall_id, st.name
        ORDER BY total_revenue_30d DESC
    """, {"cid": campus_id, "cat": category, "sid": stall_id})
    
    return {
        "competitors_df": competitors,
        "campus_id": campus_id,
        "category": category,
    }

@st.cache_data(ttl=300, show_spinner=False)
def get_stall_metrics_summary_for_ai(stall_id: int) -> str:
    """Get comprehensive 30-day metrics summary for the stall."""
    # Overall metrics
    metrics = fetch_data("""
        SELECT 
            COUNT(DISTINCT o.order_id) AS total_orders,
            SUM(CASE WHEN o.delivery_status='Completed' THEN 1 ELSE 0 END) AS completed_orders,
            SUM(CASE WHEN o.delivery_status='Canceled' THEN 1 ELSE 0 END) AS cancelled_orders,
            ROUND(100.0 * SUM(CASE WHEN o.delivery_status='Completed' THEN 1 ELSE 0 END) 
                / NULLIF(COUNT(DISTINCT o.order_id), 0), 1) AS completion_rate,
            ROUND(SUM(o.total_amount), 0) AS total_revenue,
            ROUND(SUM(o.subtotal), 0) AS subtotal_amount,
            ROUND(SUM(o.gst_amount), 0) AS total_gst,
            ROUND(SUM(o.tip_amount), 0) AS total_tips,
            ROUND(AVG(r.rating), 2) AS avg_rating,
            COUNT(DISTINCT r.review_id) AS total_reviews,
            SUM(CASE WHEN r.rating = 5 THEN 1 ELSE 0 END) AS five_star_count,
            SUM(CASE WHEN r.rating = 4 THEN 1 ELSE 0 END) AS four_star_count,
            SUM(CASE WHEN r.rating = 3 THEN 1 ELSE 0 END) AS three_star_count,
            SUM(CASE WHEN r.rating <= 2 THEN 1 ELSE 0 END) AS poor_rating_count
        FROM Orders o
        LEFT JOIN Reviews r ON o.order_id = r.order_id AND r.item_id IS NULL
        WHERE o.stall_id = :sid
          AND o.order_time >= DATE('now','-14 days')
    """, {"sid": stall_id})
    
    # Top performing items
    top_items = fetch_data("""
        SELECT 
            i.name AS item_name,
            COUNT(oi.order_item_id) AS times_ordered,
            ROUND(SUM(oi.unit_price * oi.quantity), 0) AS item_revenue,
            ROUND(AVG(r.rating), 2) AS avg_item_rating,
            COUNT(DISTINCT r.review_id) AS item_reviews
        FROM Order_Items oi
        JOIN Orders o ON oi.order_id = o.order_id
        JOIN Items i ON oi.item_id = i.item_id
        LEFT JOIN Reviews r ON o.order_id = r.order_id AND r.item_id = i.item_id
        WHERE o.stall_id = :sid
          AND o.order_time >= DATE('now','-14 days')
          AND o.delivery_status = 'Completed'
        GROUP BY i.item_id, i.name
        ORDER BY item_revenue DESC
        LIMIT 10
    """, {"sid": stall_id})
    
    # Category breakdown
    category_breakdown = fetch_data("""
        SELECT 
            i.category,
            COUNT(DISTINCT o.order_id) AS category_orders,
            ROUND(SUM(oi.unit_price * oi.quantity), 0) AS category_revenue,
            ROUND(AVG(r.rating), 2) AS category_avg_rating
        FROM Order_Items oi
        JOIN Orders o ON oi.order_id = o.order_id
        JOIN Items i ON oi.item_id = i.item_id
        LEFT JOIN Reviews r ON o.order_id = r.order_id
        WHERE o.stall_id = :sid
          AND o.order_time >= DATE('now','-14 days')
          AND o.delivery_status = 'Completed'
        GROUP BY i.category
        ORDER BY category_revenue DESC
    """, {"sid": stall_id})
    
    # Build formatted summary
    summary = "=== 30-DAY STALL PERFORMANCE METRICS ===\n"
    
    if not metrics.empty:
        m = metrics.iloc[0]
        summary += f"""
📊 ORDER METRICS:
  • Total Orders: {int(m['total_orders'])}
  • Completed Orders: {int(m['completed_orders'])}
  • Cancelled Orders: {int(m['cancelled_orders'])}
  • Completion Rate: {m['completion_rate']}%

💰 REVENUE METRICS:
  • Total Revenue: PKR {int(m['total_revenue']):,}
  • Subtotal (pre-GST): PKR {int(m['subtotal_amount']):,}
  • GST Collected: PKR {int(m['total_gst']):,}
  • Tips Received: PKR {int(m['total_tips']):,}
  • Avg Revenue per Order: PKR {int(m['total_revenue'] / max(m['total_orders'], 1)):,}

⭐ RATING & REVIEWS:
  • Average Rating: {m['avg_rating']}/5.0
  • Total Reviews: {int(m['total_reviews'])}
  • 5-Star Reviews: {int(m['five_star_count'])}
  • 4-Star Reviews: {int(m['four_star_count'])}
  • 3-Star Reviews: {int(m['three_star_count'])}
  • Low Rating (1-2 stars): {int(m['poor_rating_count'])}
"""
    
    if not top_items.empty:
        summary += "\n🏆 TOP PERFORMING ITEMS:\n"
        for idx, item in top_items.iterrows():
            summary += f"  {idx+1}. {item['item_name']}: {int(item['times_ordered'])} orders, PKR {int(item['item_revenue']):,} revenue, {item['avg_item_rating']}/5 rating\n"
    
    if not category_breakdown.empty:
        summary += "\n📂 REVENUE BY CATEGORY:\n"
        for idx, cat in category_breakdown.iterrows():
            summary += f"  • {cat['category']}: {int(cat['category_orders'])} orders, PKR {int(cat['category_revenue']):,}, {cat['category_avg_rating']}/5 rating\n"
    
    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# ── ML HELPERS ────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def _prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, LabelEncoder | None]:
    """Build feature matrix from raw orders DataFrame."""
    # Aggregate to hourly buckets for training target
    df["order_time"] = pd.to_datetime(df["order_time"])
    df["date"] = df["order_time"].dt.date

    daily = (
        df[df["delivery_status"] == "Completed"]
        .groupby(["date", "dow", "month"])
        .agg(order_count=("order_id", "count"))
        .reset_index()
    )
    daily["day_num"] = range(len(daily))

    le = None
    if "category" in df.columns and df["category"].nunique() > 1:
        le = LabelEncoder()
        cat_mode = (
            df.groupby("date")["category"].agg(lambda x: x.mode()[0])
              .reset_index()
              .rename(columns={"category": "top_cat"})
        )
        daily = daily.merge(cat_mode, on="date", how="left")
        daily["top_cat_enc"] = le.fit_transform(daily["top_cat"].fillna("Unknown"))
        features = ["dow", "month", "day_num", "top_cat_enc"]
    else:
        features = ["dow", "month", "day_num"]

    daily = daily.dropna(subset=features + ["order_count"])
    return daily, le, features


@st.cache_data(ttl=300, show_spinner=False)
def get_item_predictions_for_scope(scope: str, scope_id: int | None, target_dow: int) -> dict:
    """
    Predict top items to be sold for a given day of week and scope.
    Returns: {item_name: predicted_quantity, ...}
    """
    if scope == "stall":
        where_scope = "WHERE o.stall_id = :sid"
        params = {"sid": scope_id}
    elif scope == "campus":
        where_scope = "WHERE st.campus_id = :cid"
        params = {"cid": scope_id}
    else:
        where_scope = ""
        params = {}

    # Get historical item sales by day of week
    item_data = fetch_data(f"""
        SELECT i.name,
               i.category,
               CAST(strftime('%w', o.order_time) AS INTEGER) AS dow,
               COUNT(oi.order_item_id) AS qty_sold,
               ROUND(AVG(oi.unit_price * oi.quantity), 0) AS avg_item_revenue
        FROM Order_Items oi
        JOIN Orders o ON oi.order_id = o.order_id
        JOIN Items i ON oi.item_id = i.item_id
        JOIN Stalls st ON o.stall_id = st.stall_id
        {where_scope}
        GROUP BY i.item_id, i.name, i.category, dow
        ORDER BY qty_sold DESC
    """, params)
    
    if item_data.empty:
        return {}
    
    # Filter for target day of week
    target_day_items = item_data[item_data["dow"] == target_dow].copy()
    
    if target_day_items.empty:
        # Fallback to overall top items
        target_day_items = item_data.groupby("name").agg({"qty_sold": "sum"}).reset_index()
    
    top_items = {}
    for _, row in target_day_items.head(5).iterrows():
        top_items[row["name"]] = int(row["qty_sold"])
    
    return top_items


@st.cache_data(ttl=600, show_spinner=False)
def get_revenue_prediction_for_scope(scope: str, scope_id: int | None, target_dow: int) -> float:
    """Predict average revenue for a given day of week."""
    if scope == "stall":
        where_clause = "WHERE o.stall_id = :sid AND o.delivery_status = 'Completed'"
        params = {"sid": scope_id}
    elif scope == "campus":
        where_clause = "WHERE st.campus_id = :cid AND o.delivery_status = 'Completed'"
        params = {"cid": scope_id}
    else:
        where_clause = "WHERE o.delivery_status = 'Completed'"
        params = {}
    
    rev_data = fetch_data(f"""
        SELECT CAST(strftime('%w', o.order_time) AS INTEGER) AS dow,
               ROUND(AVG(o.total_amount), 0) AS avg_revenue
        FROM Orders o
        JOIN Stalls st ON o.stall_id = st.stall_id
        {where_clause}
        GROUP BY dow
    """, params)
    
    if not rev_data.empty:
        target_row = rev_data[rev_data["dow"] == target_dow]
        if not target_row.empty:
            return float(target_row.iloc[0]["avg_revenue"])
    
    return 0.0


@st.cache_data(ttl=600, show_spinner=False)
def get_dow_predictions(scope: str, scope_id: int | None) -> dict:
    """
    Get 7-day predictions based on historical day-of-week averages.
    Returns: {day_name: predicted_orders, ...}
    """
    if scope == "stall":
        where_clause = "WHERE o.stall_id = :sid AND o.delivery_status = 'Completed'"
        params = {"sid": scope_id}
    elif scope == "campus":
        where_clause = "WHERE st.campus_id = :cid AND o.delivery_status = 'Completed'"
        params = {"cid": scope_id}
    else:
        where_clause = "WHERE o.delivery_status = 'Completed'"
        params = {}
    
    # Get average orders by day of week
    dow_data = fetch_data(f"""
        SELECT CAST(strftime('%w', o.order_time) AS INTEGER) AS dow,
               ROUND(AVG(COUNT(o.order_id)) OVER (PARTITION BY strftime('%w', o.order_time)), 0) AS avg_orders
        FROM Orders o
        JOIN Stalls st ON o.stall_id = st.stall_id
        {where_clause}
        GROUP BY strftime('%Y-%m-%d', o.order_time)
    """, params)
    
    if dow_data.empty:
        return {}
    
    # Aggregate to get average per day of week
    dow_avg = dow_data.groupby("dow")["avg_orders"].mean().to_dict()
    
    # Generate 7-day forecast starting from today
    import datetime
    predictions = {}
    today = datetime.date.today()
    
    for i in range(7):
        future_date = today + datetime.timedelta(days=i)
        dow = future_date.weekday() + 1  # strftime %w format
        if dow == 7:
            dow = 0
        
        pred_val = int(dow_avg.get(dow, 50))  # Default to 50 if no data
        predictions[future_date.strftime("%a %d %b")] = max(0, pred_val)
    
    return predictions


@st.cache_data(ttl=600, show_spinner=False)
def train_and_predict(scope: str, scope_id: int | None) -> dict:
    """Train RandomForestRegressor and return predictions + diagnostics."""
    raw = get_orders_for_ml(scope, scope_id)
    if raw.empty or len(raw) < 30:
        return {"error": "Not enough historical data to train a model (need ≥ 30 orders)."}

    try:
        daily, le, features = _prepare_features(raw)

        X = daily[features].values
        y = daily["order_count"].values

        if len(X) < 10:
            return {"error": "Insufficient daily data points after aggregation."}

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)
        model.fit(X_tr, y_tr)
        mae = mean_absolute_error(y_te, model.predict(X_te))

        # Predict next 7 days
        import datetime
        today_dow = datetime.date.today().weekday() + 1  # Mon=1 … Sun=0 (strftime %w style)
        today_month = datetime.date.today().month
        last_day_num = int(daily["day_num"].max())
        predictions = []
        for i in range(1, 8):
            future_dow = (today_dow + i) % 7
            future_month = today_month  # simplified
            future_day_num = last_day_num + i
            if le is not None:
                # Use most common category as fallback
                most_common_cat_enc = int(daily["top_cat_enc"].mode()[0])
                feat = [future_dow, future_month, future_day_num, most_common_cat_enc]
            else:
                feat = [future_dow, future_month, future_day_num]
            pred = max(0, int(model.predict([feat])[0]))
            predictions.append({
                "day": (datetime.date.today() + datetime.timedelta(days=i)).strftime("%a %d %b"),
                "predicted_orders": pred,
            })

        # Feature importances
        imp = dict(zip(features, model.feature_importances_))

        return {
            "predictions": predictions,
            "mae": round(mae, 1),
            "training_days": len(daily),
            "feature_importances": imp,
            "historical_daily": daily[["date", "order_count"]].tail(30),
        }

    except Exception as exc:
        return {"error": str(exc)}


@st.cache_data(ttl=600, show_spinner=False)
def get_hourly_predictions(scope: str, scope_id: int | None, target_dow: int, target_hour: int) -> dict:
    """Get hourly-based predictions for orders, revenue, and top items."""
    if scope == "stall":
        where_clause = "WHERE o.stall_id = :sid AND o.delivery_status = 'Completed'"
        item_where = "AND o.stall_id = :sid"
        params = {"sid": scope_id}
    elif scope == "campus":
        where_clause = "WHERE st.campus_id = :cid AND o.delivery_status = 'Completed'"
        item_where = "AND st.campus_id = :cid"
        params = {"cid": scope_id}
    else:
        where_clause = "WHERE o.delivery_status = 'Completed'"
        item_where = ""
        params = {}
    
    # Get historical hourly orders for this day-of-week and hour
    hourly_orders = fetch_data(f"""
        SELECT CAST(strftime('%w', o.order_time) AS INTEGER) AS dow,
               CAST(strftime('%H', o.order_time) AS INTEGER) AS hour,
               COUNT(o.order_id) AS order_count,
               ROUND(AVG(o.total_amount), 0) AS avg_order_value
        FROM Orders o
        JOIN Stalls st ON o.stall_id = st.stall_id
        {where_clause}
        GROUP BY dow, hour
    """, params)
    
    # Filter for target day and hour
    target_data = hourly_orders[
        (hourly_orders["dow"] == target_dow) & 
        (hourly_orders["hour"] == target_hour)
    ]
    
    if target_data.empty:
        # Fallback to average for this hour across all days
        target_data = hourly_orders[hourly_orders["hour"] == target_hour]
    
    if target_data.empty:
        return {
            "predicted_orders": 0,
            "avg_order_value": 0,
            "top_items": {},
            "total_revenue": 0
        }
    
    predicted_orders = int(target_data["order_count"].mean())
    avg_order_value = int(target_data["avg_order_value"].mean())
    total_revenue = predicted_orders * avg_order_value
    
    # Get top items for this hour
    item_query = f"""
        SELECT i.name,
               COUNT(oi.order_item_id) AS qty_sold
        FROM Order_Items oi
        JOIN Orders o ON oi.order_id = o.order_id
        JOIN Items i ON oi.item_id = i.item_id
        JOIN Stalls st ON o.stall_id = st.stall_id
        WHERE CAST(strftime('%H', o.order_time) AS INTEGER) = :hour
          AND CAST(strftime('%w', o.order_time) AS INTEGER) = :dow
          {item_where}
        GROUP BY i.item_id, i.name
        ORDER BY qty_sold DESC
        LIMIT 5
    """
    item_params = {**params, "hour": target_hour, "dow": target_dow}
    top_items_df = fetch_data(item_query, item_params)
    
    top_items = {}
    if not top_items_df.empty:
        for _, row in top_items_df.iterrows():
            top_items[row["name"]] = int(row["qty_sold"])
    
    return {
        "predicted_orders": predicted_orders,
        "avg_order_value": avg_order_value,
        "top_items": top_items,
        "total_revenue": total_revenue
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ── SECTION: SALES FORECASTER ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
if section == "🔮 Sales Forecaster":
    st.title("🔮 ML Sales Forecaster")

    # Scope label
    if role == "admin":
        scope = "platform"
        scope_id = None
        scope_label = "Platform-wide"
    elif role == "incharge":
        scope = "campus"
        scope_id = int(campus_id)
        campuses = get_all_campuses()
        cname = campuses.loc[campuses["campus_id"] == scope_id, "name"].values
        scope_label = f"{cname[0]} Campus" if len(cname) else "Campus"
    else:
        scope = "stall"
        scope_id = int(entity_id)
        sname_df = fetch_data("SELECT name FROM Stalls WHERE stall_id = :sid", {"sid": scope_id})
        scope_label = sname_df.iloc[0]["name"] if not sname_df.empty else "Your Stall"

    st.markdown(f"**Prediction scope:** `{scope_label}`")
    st.info(
        "This model uses a **RandomForestRegressor** trained on historical order data. "
        "Features include: day of week, month, and cumulative day number. "
        "Select a specific date below to get item-level predictions and personalized recommendations."
    )

    # ── DATE/TIME SELECTION ───────────────────────────────────────────────────
    import datetime
    col_date, col_hour = st.columns(2)
    
    with col_date:
        prediction_date = st.date_input(
            "📅 Select Prediction Date",
            value=datetime.date.today() + datetime.timedelta(days=1),
            min_value=datetime.date.today(),
            max_value=datetime.date.today() + datetime.timedelta(days=30)
        )
    
    with col_hour:
        hour_options = [f"{h:02d}:00" for h in range(24)]
        selected_hour_str = st.selectbox(
            "🕐 Select Hour",
            hour_options,
            index=12
        )
        prediction_hour = int(selected_hour_str.split(":")[0])
    
    st.divider()

    with st.spinner("🧠 Training model & generating predictions..."):
        result = train_and_predict(scope, scope_id)

    if "error" in result:
        st.error(f"⚠️ {result['error']}")
    else:
        # Get target day of week (0=Monday, 6=Sunday for strftime %w shows 0=Sunday, 1=Monday...)
        target_dow = prediction_date.weekday() + 1  # Convert to strftime format
        if target_dow == 7:
            target_dow = 0
        
        # Get hourly predictions for the selected date and hour
        hourly_pred = get_hourly_predictions(scope, scope_id, target_dow, prediction_hour)
        selected_pred = hourly_pred["predicted_orders"]
        avg_revenue = hourly_pred["avg_order_value"]
        top_items = hourly_pred["top_items"]
        total_revenue = hourly_pred["total_revenue"]

        # ── PREDICTIONS DISPLAY ───────────────────────────────────────────────
        st.subheader(f"📊 Predictions for {prediction_date.strftime('%A, %d %B %Y')} at {selected_hour_str}")
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📦 Predicted Orders/Hour", f"{selected_pred:,}", delta=None)
        k2.metric("💰 Avg Revenue/Order", f"PKR {avg_revenue:,.0f}" if avg_revenue > 0 else "N/A")
        k3.metric("💵 Estimated Hourly Revenue", f"PKR {total_revenue:,.0f}" if total_revenue > 0 else "N/A")
        k4.metric("📊 Based on", f"Historical {24} hours")

        st.markdown("---")

        # ── TOP ITEMS PREDICTION ──────────────────────────────────────────────
        if top_items:
            st.subheader("🏆 Top Items Likely to Sell This Hour")
            
            item_cols = st.columns(min(3, len(top_items)))
            for idx, (item_name, qty) in enumerate(list(top_items.items())[:3]):
                with item_cols[idx % 3]:
                    st.metric(
                        f"#{idx + 1}: {item_name}",
                        f"~{qty} units",
                        delta=f"Based on {item_name} historical sales pattern"
                    )
            st.markdown("---")

        # ── ROLE-SPECIFIC RECOMMENDATIONS ────────────────────────────────────
        day_name = prediction_date.strftime("%A")
        
        if role == "owner":
            aov_df = fetch_data(
                "SELECT AVG(total_amount) AS aov FROM Orders WHERE stall_id = :sid "
                "AND delivery_status='Completed'",
                {"sid": scope_id},
            )
            aov = aov_df.iloc[0]["aov"] if not aov_df.empty else avg_revenue

            colors = get_advice_box_colors()
            st.markdown(
                f"""
                <div style="background:{colors['bg']}; border-left: 4px solid {colors['border']};
                     padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="color:{GREEN}; margin:0 0 0.5rem;">🤖 Stall Prep Advice for {day_name} {selected_hour_str}</h4>
                <p style="margin:0; color:{colors['text']};">
                📦 Expected hourly orders: <strong>{selected_pred:,}</strong><br>
                💰 Estimated hourly revenue: <strong>PKR {selected_pred * aov:,.0f}</strong><br>
                📍 Top sellers this hour: <strong>{', '.join(list(top_items.keys())[:3]) if top_items else 'N/A'}</strong><br>
                {'🔥 <strong>Peak hour</strong> — ensure {", ".join(list(top_items.keys())[:2])} are fully stocked. Full staffing recommended.' if selected_pred > 20 
                 else ('⚡ <strong>Busy hour</strong> — prepare standard inventory levels.' if selected_pred > 10
                 else '📉 <strong>Quiet hour</strong> — routine operations sufficient.')}
                </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif role == "incharge":
            colors = get_advice_box_colors()
            st.markdown(
                f"""
                <div style="background:{colors['bg']}; border-left: 4px solid {colors['border']};
                     padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="color:{GREEN}; margin:0 0 0.5rem;">📍 Campus Operations Outlook for {day_name} {selected_hour_str}</h4>
                <p style="margin:0; color:{colors['text']};">
                🎯 Campus-wide hourly orders: <strong>{selected_pred:,}</strong><br>
                💵 Expected hourly revenue: <strong>PKR {total_revenue:,.0f}</strong><br>
                👥 {'Peak hour — ensure maximum rider capacity and delivery coordination.' if selected_pred > 50 
                 else ('Standard hour — regular rider availability sufficient.' if selected_pred > 20
                 else 'Low traffic hour — standard operations.')}
                </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:  # admin
            colors = get_advice_box_colors()
            st.markdown(
                f"""
                <div style="background:{colors['bg']}; border-left: 4px solid {colors['border']};
                     padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="color:{GREEN}; margin:0 0 0.5rem;">🌍 Platform Forecast for {day_name} {selected_hour_str}</h4>
                <p style="margin:0; color:{colors['text']};">
                📊 Platform hourly orders: <strong>{selected_pred:,}</strong><br>
                💰 Estimated hourly revenue: <strong>PKR {total_revenue:,.0f}</strong><br>
                🎯 Top items this hour: <strong>{', '.join(list(top_items.keys())[:3]) if top_items else 'N/A'}</strong>
                </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── 7-Day Forecast Bar Chart ──────────────────────────────────────────
        st.subheader("📅 7-Day Order Volume Forecast")
        
        # Get day-of-week based predictions
        dow_preds = get_dow_predictions(scope, scope_id)
        if dow_preds:
            dow_df = pd.DataFrame(list(dow_preds.items()), columns=["day", "predicted_orders"])
        else:
            dow_df = pd.DataFrame(preds)
        
        fig_pred = go.Figure(go.Bar(
            x=dow_df["day"],
            y=dow_df["predicted_orders"],
            marker_color=[GREEN if i == 0 else ORANGE for i in range(len(dow_df))],
            text=dow_df["predicted_orders"],
            textposition="outside",
        ))
        fig_pred = styled_chart(fig_pred)
        st.plotly_chart(fig_pred, use_container_width=True)

        # ── Historical vs Trend ───────────────────────────────────────────────
        hist_df = result.get("historical_daily")
        if hist_df is not None and not hist_df.empty:
            st.subheader("📜 Historical Daily Orders (Last 14 Days)")
            hist_df["date"] = hist_df["date"].astype(str)
            fig_hist = go.Figure(go.Scatter(
                x=hist_df["date"], y=hist_df["order_count"],
                mode="lines+markers",
                line=dict(color=ORANGE, width=2),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor="rgba(255,107,53,0.1)",
            ))
            fig_hist = styled_chart(fig_hist)
            st.plotly_chart(fig_hist, use_container_width=True)

        # ── Feature Importances ───────────────────────────────────────────────
        with st.expander("🔬 Model Feature Importances", expanded=False):
            feat_imp = result.get("feature_importances", {})
            if feat_imp:
                imp_df = pd.DataFrame(
                    list(feat_imp.items()), columns=["Feature", "Importance"]
                ).sort_values("Importance", ascending=True)
                fig_imp = px.bar(
                    imp_df, x="Importance", y="Feature", orientation="h",
                    color="Importance",
                    color_continuous_scale=[[0, YELLOW], [1, ORANGE]],
                    text_auto=".3f",
                )
                fig_imp = styled_chart(fig_imp)
                fig_imp.update_layout(coloraxis_showscale=False, yaxis_title="")
                st.plotly_chart(fig_imp, use_container_width=True)
            st.caption(f"Model trained on {result['training_days']} daily data points.")


# ═══════════════════════════════════════════════════════════════════════════════
# ── SECTION: AI BUSINESS ADVISOR ─────────────────────────════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
elif section == "🤖 AI Business Advisor":
    st.title("🤖 AI Business Advisor")
    st.caption(
        "Ask anything about your business performance, competitive positioning, and customer sentiment. "
        "The advisor analyses your last 14 days of data, reviews, ratings, and competitor benchmarks to give actionable advice."
    )

    # ── Stall context for AI prompt ───────────────────────────────────────────
    # Determine which stall to use for context
    if role == "owner":
        advisor_stall_id = int(entity_id)
    else:
        stalls_df = fetch_data(
            "SELECT stall_id, name FROM Stalls"
            + (" WHERE campus_id = :cid" if role == "incharge" else ""),
            {"cid": int(campus_id)} if role == "incharge" else {},
        )
        if stalls_df.empty:
            st.error("No stalls found.")
            st.stop()
        stall_map = {row["name"]: row["stall_id"] for _, row in stalls_df.iterrows()}
        chosen = st.selectbox("🍽️ Analyse stall:", list(stall_map.keys()))
        advisor_stall_id = int(stall_map[chosen])

    # Load context silently
    context_df = get_stall_context_for_ai(advisor_stall_id)
    context_csv = context_df.to_csv(index=False) if not context_df.empty else "No data available."
    
    # Load comprehensive metrics summary
    metrics_summary = get_stall_metrics_summary_for_ai(advisor_stall_id)
    
    # Load reviews data
    reviews_df = get_stall_reviews_for_ai(advisor_stall_id)
    reviews_summary = f"""
Total Reviews (14 days): {len(reviews_df)}
Avg Rating: {reviews_df['rating'].mean():.2f}/5.0
Rating Breakdown: {reviews_df['rating'].value_counts().to_dict()}
"""
    
    # Load competitive data
    competitor_data = get_competitive_stalls_for_ai(advisor_stall_id)
    competitors_df = competitor_data["competitors_df"]
    competitors_csv = competitors_df.to_csv(index=False) if not competitors_df.empty else "No competitors found."

    stall_info_df = fetch_data(
        "SELECT name, category FROM Stalls WHERE stall_id = :sid",
        {"sid": advisor_stall_id},
    )
    stall_display_name = stall_info_df.iloc[0]["name"] if not stall_info_df.empty else "the stall"
    stall_category = stall_info_df.iloc[0]["category"] if not stall_info_df.empty else "food"

    # ── Context preview ───────────────────────────────────────────────────────
    with st.expander("📊 Data being sent to AI (last 14 days)", expanded=False):
        st.subheader("📈 Comprehensive Performance Metrics")
        st.text(metrics_summary)
        
        st.markdown("---")
        
        st.subheader("📊 Daily Financial Performance (14 Days)")
        if not context_df.empty:
            st.dataframe(context_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent data available for this stall.")
        
        st.markdown("---")
        
        st.subheader("⭐ Customer Reviews & Ratings (14 Days)")
        st.metric("Total Reviews", len(reviews_df))
        if not reviews_df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg Rating", f"{reviews_df['rating'].mean():.2f}/5.0")
            col2.metric("5-Star Reviews", (reviews_df['rating'] == 5).sum())
            col3.metric("1-2 Star Reviews", (reviews_df['rating'] <= 2).sum())
            st.dataframe(reviews_df[['rating', 'item_name', 'comment', 'review_time']], 
                        use_container_width=True, hide_index=True)
        else:
            st.info("No reviews yet for this stall.")
        
        st.markdown("---")
        
        st.subheader(f"🏆 Competitive Benchmarks ({stall_category} category, same campus, 14 Days)")
        if not competitors_df.empty:
            st.dataframe(competitors_df, use_container_width=True, hide_index=True)
        else:
            st.info("No competitor data available or you're the only stall in this category on campus.")

    st.markdown("---")

    # ── Chat Interface ─────────────────────────────────────────────────────────
    # Check for API key
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        st.warning(
            "⚠️ **Gemini API key not configured.** "
            "Please set `GEMINI_API_KEY` in your `.env` file to enable the AI Advisor. "
            "Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)."
        )
        st.stop()

    # Initialise chat history and response cache in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "ai_response_cache" not in st.session_state:
        st.session_state.ai_response_cache = {}
    
    if "last_api_error_time" not in st.session_state:
        st.session_state.last_api_error_time = None
    
    if "processing_message" not in st.session_state:
        st.session_state.processing_message = False

    # Render existing messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Starter suggestions
    if not st.session_state.chat_history:
        st.markdown("**💡 Try asking:**")
        suggestions = [
            "Why did my revenue drop this week?",
            "Which items should I promote next week?",
            "What is my busiest day and how should I prepare?",
            "How can I reduce my cancellation rate?",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            if cols[i % 2].button(f"💬 {s}", key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_question = s
                st.rerun()

    # Auto-fill from suggestion click
    user_input = st.chat_input("Ask your AI Business Advisor anything...")
    if "pending_question" in st.session_state and st.session_state.pending_question:
        user_input = st.session_state.pending_question
        del st.session_state.pending_question

    if user_input:
        # Prevent double-processing the same message
        if st.session_state.processing_message:
            st.stop()
        
        st.session_state.processing_message = True
        
        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build system prompt
        system_prompt = f"""You are a data-driven business advisor for CampusEats, a university food delivery platform in Pakistan. Analyze {stall_display_name} ({stall_category}) data and provide actionable insights.

METRICS: {metrics_summary}

DAILY DATA (14 DAYS): {context_csv}

REVIEWS: {reviews_summary}

COMPETITORS (SAME CATEGORY): {competitors_csv}

GUIDELINES:
- Give concise, specific recommendations with actual numbers
- Use bullet points for actions
- Compare against competitor averages
- Reference both strengths and areas to improve
- Format money in PKR
- If data is sparse, give general best practices
- End with one bold Key Takeaway"""

        # Build message history for Gemini (reduce from 8 to 3 turns to save tokens)
        api_messages = []
        for past_msg in st.session_state.chat_history[-3:]:
            api_messages.append({
                "role": past_msg["role"],
                "parts": [{"text": past_msg["content"]}],
            })

        # ── Call Gemini API with Caching ────────────────────────────────────────
        with st.chat_message("assistant"):
            with st.spinner("🤖 Analysing your data..."):
                reply = None
                
                # Get current user question for cache lookup
                current_question = None
                for m in reversed(api_messages):
                    if m["role"] == "user":
                        current_question = m["parts"][0].get("text", "").strip()
                        break
                
                # Check if we have a cached response for this question
                cache_key = hash(current_question) if current_question else None
                if cache_key and cache_key in st.session_state.ai_response_cache:
                    reply = st.session_state.ai_response_cache[cache_key]
                    st.info("💾 Using cached response (from earlier in this session)")
                else:
                    # Try API call
                    try:
                        import google.generativeai as genai

                        genai.configure(api_key=gemini_key)
                        # Use gemini-2.5-flash (shown in your quota dashboard)
                        gemini_model = genai.GenerativeModel(
                            model_name="gemini-2.5-flash",
                            system_instruction=system_prompt,
                        )
                        
                        if not current_question:
                            reply = "⚠️ Unable to process your message. Please try again."
                        else:
                            # Send question directly as text
                            response = gemini_model.generate_content(current_question)
                            
                            if response and hasattr(response, 'text') and response.text:
                                reply = response.text
                                # Cache successful response
                                if cache_key:
                                    st.session_state.ai_response_cache[cache_key] = reply
                            else:
                                reply = "⚠️ AI returned empty response. Please try again."
                            
                    except Exception as exc:
                        err_str = str(exc)
                        
                        # Specific error handling
                        if "429" in err_str:
                            reply = (
                                "⏳ **API Rate Limit Reached**\n\n"
                                "The Gemini API is temporarily rate-limited (free tier quota). "
                                "This is normal with high usage.\n\n"
                                "**Solutions:**\n"
                                "1. ⏰ **Wait 5-10 minutes** - quotas reset periodically\n"
                                "2. 🧹 **Clear conversation** to reduce token usage\n"
                                "3. 💾 **Ask simpler questions** - fewer tokens = faster responses\n"
                                "4. 💳 **Upgrade your API plan** at [Google AI Studio](https://aistudio.google.com/) for higher limits\n\n"
                                "Try again after a short wait!"
                            )
                        elif "API_KEY" in err_str.upper() or "api key" in err_str.lower() or "not authenticated" in err_str.lower():
                            reply = (
                                "🔑 **Invalid or Missing API Key**\n\n"
                                "Please check your `.env` file and restart the app."
                            )
                        elif "not found" in err_str.lower() or "404" in err_str:
                            reply = (
                                "⚠️ **Model Not Found**\n\n"
                                "The Gemini model (gemini-2.5-flash) is not available or your API key doesn't have access to it. "
                                "Please verify your API key at [Google AI Studio](https://aistudio.google.com/)."
                            )
                        elif "SAFETY" in err_str.upper():
                            reply = (
                                "🛡️ **Safety Filter Triggered**\n\n"
                                "The AI Advisor declined to respond for safety reasons. "
                                "Please rephrase your question."
                            )
                        else:
                            reply = (
                                f"⚠️ **API Error**: {err_str[:150]}\n\n"
                                "Please try a simpler question or check your API configuration."
                            )

            st.markdown(reply if reply else "⚠️ Unable to get response. Please try again.")
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": reply if reply else "⚠️ Unable to get response from AI Advisor."
            })
        
        # Reset processing flag to allow next message
        st.session_state.processing_message = False

    # ── Clear chat button ──────────────────────────────────────────────────────
    if st.session_state.chat_history:
        st.markdown("---")
        if st.button("🗑️ Clear conversation", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()
