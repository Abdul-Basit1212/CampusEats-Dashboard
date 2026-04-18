"""
pages/3_🏪_Stall_Dashboard.py — CampusEats Dashboard
Stall Owner View: Financial analytics, rush hour heatmap, menu intelligence,
customer feedback.
Access: all roles (scoped to stall).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from database import fetch_data, get_all_campuses
from security import validate_session, authorize_stall_access, log_audit

# ── Page config & auth guard ──────────────────────────────────────────────────
st.set_page_config(page_title="Stall Dashboard · CampusEats", page_icon="🏪", layout="wide")

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

# ── Theme Support Functions ───────────────────────────────────────────────────
def get_chart_template():
    """Return chart template based on Streamlit theme."""
    return "plotly_dark" if st.get_option("theme.base") == "dark" else "plotly"

def styled_chart(fig, template=None):
    """Apply consistent theming to chart."""
    if template is None:
        template = get_chart_template()
    fig.update_layout(template=template)
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏪 Stall Dashboard")
    st.divider()
    st.markdown(f"### 👋 {st.session_state.user_name}")
    role_icons = {"admin": "🌍 Global Admin", "incharge": "📍 Campus Incharge", "owner": "🏪 Stall Owner"}
    st.markdown(f"**Role:** {role_icons.get(st.session_state.user_role, '')}")
    st.divider()
    page = st.radio(
        "Navigate",
        ["💰 Financial Analytics", "📊 Menu Intelligence", "💬 Customer Feedback"],
        label_visibility="collapsed",
    )
    st.divider()
    
    # Campus Selector (for admin/incharge)
    role = st.session_state.user_role
    if role in ("admin", "incharge"):
        campuses_df = fetch_data("SELECT campus_id, name FROM Campuses ORDER BY name", {})
        if not campuses_df.empty:
            campus_options = {row["name"]: row["campus_id"] for _, row in campuses_df.iterrows()}
            selected_campus_name = st.selectbox("🏫 Select Campus", list(campus_options.keys()))
            active_campus_id = int(campus_options[selected_campus_name])
        else:
            st.error("No campuses found.")
            st.stop()
    else:
        # Owner: get campus from their stall
        cursor_owner = fetch_data("SELECT campus_id FROM Stalls WHERE stall_id = :sid", 
                                  {"sid": int(st.session_state.entity_id)})
        active_campus_id = cursor_owner.iloc[0]["campus_id"] if not cursor_owner.empty else 1
    
    # Stall Selector
    if role == "owner":
        active_stall_id = int(st.session_state.entity_id)
        stall_info_df = fetch_data(
            """SELECT name, campus_id FROM Stalls WHERE stall_id = :sid""", 
            {"sid": active_stall_id}
        )
        if not stall_info_df.empty:
            active_stall_name = stall_info_df.iloc[0]["name"]
            campus_name_df = fetch_data(
                "SELECT name FROM Campuses WHERE campus_id = :cid", 
                {"cid": int(stall_info_df.iloc[0]["campus_id"])}
            )
            campus_name = campus_name_df.iloc[0]["name"] if not campus_name_df.empty else "Unknown"
        else:
            active_stall_name = "Your Stall"
            campus_name = "Unknown"
    else:
        stalls_df = fetch_data(
            """SELECT stall_id, name, campus_id FROM Stalls 
               WHERE campus_id = :cid ORDER BY name""",
            {"cid": active_campus_id},
        )
        if not stalls_df.empty:
            campus_name_df = fetch_data(
                "SELECT name FROM Campuses WHERE campus_id = :cid", 
                {"cid": active_campus_id}
            )
            campus_name = campus_name_df.iloc[0]["name"] if not campus_name_df.empty else "Unknown"
            
            stall_options = {f"{row['name']}": row["stall_id"]
                           for _, row in stalls_df.iterrows()}
            selected_label = st.selectbox("🍽️ Select Stall", list(stall_options.keys()))
            active_stall_id = int(stall_options[selected_label])
            active_stall_name = selected_label
        else:
            st.error("No stalls found for this campus.")
            st.stop()
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("Home.py")

# ═══════════════════════════════════════════════════════════════════════════════
# ── DATA FETCHERS (all scoped to stall_id) ───────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_financial_kpis(stall_id: int):
    return fetch_data("""
        SELECT
            COALESCE(SUM(CASE WHEN DATE(order_time)=DATE('now')
                         THEN subtotal ELSE 0 END), 0)      AS today_subtotal,
            COALESCE(SUM(CASE WHEN DATE(order_time)=DATE('now')
                         THEN gst_amount ELSE 0 END), 0)    AS today_gst,
            COALESCE(SUM(CASE WHEN DATE(order_time)=DATE('now')
                         THEN tip_amount ELSE 0 END), 0)    AS today_tips,
            COALESCE(SUM(CASE WHEN DATE(order_time)=DATE('now')
                         THEN total_amount ELSE 0 END), 0)  AS today_total,
            COALESCE(SUM(subtotal), 0)                      AS all_time_revenue,
            COUNT(DISTINCT CASE WHEN delivery_status='Completed'
                           THEN order_id END)               AS completed_orders
        FROM Orders
        WHERE stall_id = :sid
          AND delivery_status = 'Completed'
    """, {"sid": stall_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_rush_hour_data(stall_id: int):
    """Return pivot table: rows=hours (0–23), cols=days (0=Mon…6=Sun)."""
    df = fetch_data("""
        SELECT
            CAST(strftime('%H', order_time) AS INTEGER) AS hour,
            CAST(strftime('%w', order_time) AS INTEGER) AS dow,
            COUNT(order_id) AS order_count
        FROM Orders
        WHERE stall_id = :sid
          AND delivery_status = 'Completed'
        GROUP BY hour, dow
    """, {"sid": stall_id})
    if df.empty:
        return pd.DataFrame()
    # dow: 0=Sun, 1=Mon … 6=Sat  → remap to Mon–Sun
    day_map = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df["day_name"] = df["dow"].map(day_map)
    pivot = df.pivot_table(index="hour", columns="day_name", values="order_count",
                           fill_value=0, aggfunc="sum")
    # Ensure all days present
    for d in day_order:
        if d not in pivot.columns:
            pivot[d] = 0
    return pivot[day_order]

@st.cache_data(ttl=300, show_spinner=False)
def get_item_revenue(stall_id: int):
    return fetch_data("""
        SELECT i.name AS item_name, i.category,
               COALESCE(SUM(oi.unit_price * oi.quantity), 0) AS revenue,
               COUNT(oi.order_item_id) AS units_sold
        FROM Items i
        JOIN Order_Items oi ON i.item_id = oi.item_id
        JOIN Orders o       ON oi.order_id = o.order_id
        WHERE i.stall_id = :sid
          AND o.delivery_status = 'Completed'
        GROUP BY i.item_id, i.name, i.category
        ORDER BY revenue DESC
    """, {"sid": stall_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_dead_weight_items(stall_id: int):
    """Items that appear in carts but have low conversion to completed orders."""
    return fetch_data("""
        SELECT i.name AS item_name, i.selling_price,
               COALESCE(cart_agg.cart_count, 0)  AS cart_appearances,
               COALESCE(order_agg.sold_count, 0) AS times_ordered
        FROM Items i
        LEFT JOIN (
            SELECT ci.item_id, COUNT(*) AS cart_count
            FROM Cart_Items ci
            GROUP BY ci.item_id
        ) cart_agg ON i.item_id = cart_agg.item_id
        LEFT JOIN (
            SELECT oi.item_id, COUNT(*) AS sold_count
            FROM Order_Items oi
            JOIN Orders o ON oi.order_id = o.order_id
            WHERE o.delivery_status = 'Completed'
            GROUP BY oi.item_id
        ) order_agg ON i.item_id = order_agg.item_id
        WHERE i.stall_id = :sid
          AND COALESCE(cart_agg.cart_count, 0) > 5
        ORDER BY cart_appearances DESC
        LIMIT 20
    """, {"sid": stall_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_customer_reviews(stall_id: int):
    return fetch_data("""
        SELECT r.review_id, i.name AS item_name,
               r.rating, r.comment, r.review_time,
               o.order_id
        FROM Reviews r
        JOIN Orders o   ON r.order_id = o.order_id
        LEFT JOIN Items i ON r.item_id = i.item_id
        WHERE o.stall_id = :sid
        ORDER BY r.review_time DESC
        LIMIT 200
    """, {"sid": stall_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_revenue_trend_30d(stall_id: int):
    return fetch_data("""
        SELECT DATE(order_time) AS order_date,
               SUM(total_amount) AS daily_revenue,
               COUNT(order_id)   AS daily_orders
        FROM Orders
        WHERE stall_id = :sid
          AND delivery_status = 'Completed'
          AND order_time >= DATE('now','-30 days')
        GROUP BY DATE(order_time)
        ORDER BY order_date
    """, {"sid": stall_id})

# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: FINANCIAL ANALYTICS ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
if page == "💰 Financial Analytics":
    st.title(f"💰 {active_stall_name} ({campus_name}) — Financial Analytics")
    st.caption("Real-time earnings breakdown and 30-day revenue trends.")

    kpi_df = get_financial_kpis(active_stall_id)
    if not kpi_df.empty:
        k = kpi_df.iloc[0]
        
        # KPI Row 1: Today's Metrics
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📦 Today's Subtotal",     f"PKR {k['today_subtotal']:,.0f}")
        k2.metric("🧾 GST Collected",        f"PKR {k['today_gst']:,.2f}")
        k3.metric("💝 Tips Earned",          f"PKR {k['today_tips']:,.2f}")
        k4.metric("🏠 Net Today",            f"PKR {k['today_total']:,.0f}")
        
        st.markdown("---")
        
        # KPI Row 2: All-Time Stats
        k5, k6 = st.columns(2)
        k5.metric("💰 All-Time Revenue",     f"PKR {k['all_time_revenue']:,.0f}")
        k6.metric("✅ Total Completed Orders", f"{k['completed_orders']:,}")
    
    st.markdown("---")

    # ── Section 1: Rush Hour Heatmap ──────────────────────────────────────────────
    st.subheader("🔥 Rush Hour Heatmap")
    st.caption("Order volume by hour of day and day of week — plan your staffing accordingly.")

    pivot = get_rush_hour_data(active_stall_id)
    if not pivot.empty:
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=[f"{h:02d}:00" for h in pivot.index],
            colorscale=[
                [0.0,  "#FAFAFA"],
                [0.25, "#FFF3E0"],
                [0.5,  YELLOW],
                [0.75, ORANGE],
                [1.0,  "#C0392B"],
            ],
            hoverongaps=False,
            hovertemplate="<b>%{y} on %{x}</b><br>Orders: %{z}<extra></extra>",
        ))
        fig_heat.update_layout(
            margin=dict(t=20, b=20, l=60, r=10),
            xaxis_title="Day of Week",
            yaxis_title="Hour of Day",
            yaxis_autorange="reversed",
        )
        st.plotly_chart(styled_chart(fig_heat), use_container_width=True)
    else:
        st.info("Not enough order data to render the heatmap yet.")

    st.markdown("---")

    # ── Section 2: 30-day Revenue Trend ─────────────────────────────────────────
    st.subheader("📈 30-Day Revenue Trend")
    trend_df = get_revenue_trend_30d(active_stall_id)
    if not trend_df.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=trend_df["order_date"], y=trend_df["daily_revenue"],
            name="Daily Revenue",
            marker_color=ORANGE, opacity=0.75,
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend_df["order_date"],
            y=trend_df["daily_revenue"].rolling(7, min_periods=1).mean(),
            name="7-Day Avg",
            line=dict(color=GREEN, width=2.5, dash="dash"),
            mode="lines",
        ))
        fig_trend.update_layout(
            margin=dict(t=10, b=20, l=10, r=10),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(styled_chart(fig_trend), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: MENU INTELLIGENCE ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Menu Intelligence":
    st.title(f"📊 {active_stall_name} ({campus_name}) — Menu Intelligence")
    st.caption("Revenue share by item, performance metrics, and dead-weight report for underperforming items.")

    item_df = get_item_revenue(active_stall_id)

    if not item_df.empty:
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("🍕 Item Revenue Share")
            # Group small items into "Other" for readability
            top_items = item_df.head(8).copy()
            if len(item_df) > 8:
                other_rev = item_df.iloc[8:]["revenue"].sum()
                top_items = pd.concat([
                    top_items,
                    pd.DataFrame([{"item_name": "Other Items", "revenue": other_rev,
                                   "category": "Other", "units_sold": 0}])
                ], ignore_index=True)

            fig_donut = go.Figure(go.Pie(
                labels=top_items["item_name"],
                values=top_items["revenue"],
                hole=0.5,
                marker_colors=[ORANGE, GREEN, YELLOW, RED,
                                "#9B59B6", "#3498DB", "#1ABC9C",
                                "#E67E22", "#95A5A6"],
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Revenue: PKR %{value:,.0f}"
                              "<br>Share: %{percent}<extra></extra>",
            ))
            fig_donut.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(styled_chart(fig_donut), use_container_width=True)

        with col_right:
            st.subheader("🏆 Top Items by Revenue")
            display = item_df.head(12)[["item_name", "category", "revenue", "units_sold"]].copy()
            display["revenue"] = display["revenue"].apply(lambda x: f"PKR {x:,.0f}")
            display.columns = ["Item", "Category", "Revenue", "Units Sold"]
            display = display.reset_index(drop=True)
            display.index += 1
            st.dataframe(display, use_container_width=True, hide_index=False, height=380)

        st.markdown("---")

        # ── Section 1: Category Revenue & Top Items ──────────────────────────────
        st.subheader("📂 Revenue by Category")
        cat_rev = item_df.groupby("category")["revenue"].sum().reset_index().sort_values(
            "revenue", ascending=True
        )
        fig_cat = px.bar(
            cat_rev, x="revenue", y="category", orientation="h",
            color="revenue",
            color_continuous_scale=[[0, YELLOW], [1, ORANGE]],
            labels={"revenue": "Revenue (PKR)", "category": "Category"},
            text_auto=".3s",
        )
        fig_cat.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            coloraxis_showscale=False, yaxis_title="",
        )
        st.plotly_chart(styled_chart(fig_cat), use_container_width=True)

    else:
        st.info("No sales data available for this stall yet.")

    st.markdown("---")

    # ── Dead Weight Report ─────────────────────────────────────────────────────
    st.subheader("☠️ Dead Weight Report")
    st.caption("Items frequently added to carts but rarely converted into completed orders. "
               "These may have pricing, image, or quality issues.")

    dead_df = get_dead_weight_items(active_stall_id)
    if not dead_df.empty:
        dead_df["conversion_rate"] = (
            dead_df["times_ordered"] / dead_df["cart_appearances"].replace(0, np.nan) * 100
        ).fillna(0).round(1)
        dead_df["selling_price"] = dead_df["selling_price"].apply(lambda x: f"PKR {x:,.0f}")
        dead_df["conversion_rate"] = dead_df["conversion_rate"].apply(lambda x: f"{x:.1f}%")
        display_dw = dead_df.rename(columns={
            "item_name": "Item", "selling_price": "Price",
            "cart_appearances": "Added to Cart", "times_ordered": "Completed Orders",
            "conversion_rate": "Conversion Rate",
        })
        st.dataframe(display_dw, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No dead weight items detected (or cart data not yet available).")


# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: CUSTOMER FEEDBACK ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💬 Customer Feedback":
    st.title(f"💬 {active_stall_name} ({campus_name}) — Customer Feedback")
    st.caption("Real-time reviews, ratings distribution, and customer sentiment analysis.")

    review_df = get_customer_reviews(active_stall_id)

    if not review_df.empty:
        # KPIs
        avg_rat  = review_df["rating"].mean()
        total_rev = len(review_df)
        five_star = (review_df["rating"] == 5).sum()

        k1, k2, k3 = st.columns(3)
        k1.metric("⭐ Average Rating", f"{avg_rat:.2f} / 5.0")
        k2.metric("📝 Total Reviews", f"{total_rev:,}")
        k3.metric("🌟 5-Star Reviews", f"{five_star:,}",
                  delta=f"{five_star/total_rev*100:.1f}% of total")

        # ── Section 1: Rating Metrics & Distribution ─────────────────────────────
        st.subheader("📊 Rating Distribution")
        dist = review_df["rating"].value_counts().sort_index()
        fig_dist = px.bar(
            x=dist.index, y=dist.values,
            labels={"x": "Stars", "y": "Count"},
            color=dist.values,
            color_continuous_scale=[[0, RED], [0.5, YELLOW], [1, GREEN]],
            text_auto=True,
        )
        fig_dist.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(tickvals=[1, 2, 3, 4, 5],
                       ticktext=["★", "★★", "★★★", "★★★★", "★★★★★"]),
            coloraxis_showscale=False,
            xaxis_title="Rating", yaxis_title="Number of Reviews",
        )
        st.plotly_chart(styled_chart(fig_dist), use_container_width=True)

        st.markdown("---")

        # Filter by rating
        rating_filter = st.slider("Filter reviews by minimum rating", 1, 5, 1)
        filtered_reviews = review_df[review_df["rating"] >= rating_filter].copy()

        filtered_reviews["Stars"] = filtered_reviews["rating"].apply(
            lambda r: "⭐" * int(r) if pd.notnull(r) else "—"
        )
        filtered_reviews["item_name"] = filtered_reviews["item_name"].fillna("General Order Review")
        filtered_reviews["comment"] = filtered_reviews["comment"].fillna("(No comment)")

        st.subheader(f"📋 Reviews (≥ {rating_filter} star{'s' if rating_filter > 1 else ''})")
        display_rev = filtered_reviews[
            ["Stars", "item_name", "comment", "review_time", "order_id"]
        ].rename(columns={
            "item_name": "Item", "comment": "Comment",
            "review_time": "Date", "order_id": "Order ID",
        })
        st.dataframe(display_rev, use_container_width=True,
                     hide_index=True, height=420)

    else:
        st.info("📭 No reviews received yet. Reviews will appear here once customers rate their orders.")
        st.markdown(
            "💡 **Tip:** Encourage customers to leave reviews by maintaining consistent food quality "
            "and ensuring timely delivery."
        )
