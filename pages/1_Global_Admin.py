"""
pages/1_🌍_Global_Admin.py — CampusEats Dashboard
Global Admin View: Platform-wide KPIs, revenue trends, campus map, system management.
Access: admin only.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
from database import fetch_data, execute_write, get_all_campuses
from security import validate_session, log_audit

# ── Page config & auth guard ──────────────────────────────────────────────────
st.set_page_config(page_title="Global Admin · CampusEats", page_icon="🌍", layout="wide")

# ⚠️ SECURITY: Validate session on EVERY page load
if not validate_session():
    st.warning("Session expired or invalid. Please login again.")
    st.switch_page("Home.py")
    st.stop()

if st.session_state.user_role != "admin":
    log_audit("unauthorized_access_attempt", f"Non-admin tried to access admin page: {st.session_state.user_role}")
    st.error("🚫 Access denied. Global Admin privileges required.")
    st.stop()

# ── Brand colours ─────────────────────────────────────────────────────────────
ORANGE  = "#FF6B35"
GREEN   = "#2EC4B6"
RED     = "#E71D36"
YELLOW  = "#FFC857"
SLATE   = "#011627"

# ── Theme detection & chart styling ────────────────────────────────────────────
def get_chart_template():
    """Get Plotly template based on Streamlit theme"""
    try:
        # Try to get theme from Streamlit config
        theme = st.get_option("theme.base") or "light"
        if theme.lower() == "dark":
            return "plotly_dark"
        else:
            return "plotly"
    except:
        return "plotly"

def styled_chart(fig, template=None):
    """Apply consistent styling to all charts with theme-aware backgrounds"""
    if template is None:
        template = get_chart_template()
    
    fig.update_layout(
        template=template,
        margin=dict(t=20, b=20, l=10, r=10),
        hovermode="x unified",
    )
    return fig

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍔 CampusEats Dashboard")
    st.divider()
    st.markdown(f"### 👋 Hello, {st.session_state.user_name}!")
    st.markdown("**Role:** 🌍 Global Admin")
    st.divider()
    page = st.radio(
        "Navigate",
        ["📊 Command Center", "🏆 Campus Showdown", "💰 Platform Economy", "⚙️ System Management"],
        label_visibility="collapsed",
    )
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("Home.py")

# ═══════════════════════════════════════════════════════════════════════════════
# ── DATA FETCHERS ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_platform_kpis():
    return fetch_data("""
        SELECT
            SUM(total_amount)                                     AS total_revenue,
            COUNT(DISTINCT s.student_id)                          AS active_students,
            AVG(o.total_amount)                                   AS avg_order_value,
            (SELECT COALESCE(SUM(amount),0) FROM Wallet_Transactions
             WHERE transaction_type = 'Top-up')                   AS total_topups,
            COUNT(DISTINCT o.order_id)                            AS total_orders,
            SUM(CASE WHEN delivery_status='Canceled' THEN 1 ELSE 0 END) * 100.0
              / COUNT(*)                                           AS cancel_rate
        FROM Orders o
        JOIN Students s ON o.student_id = s.student_id
        WHERE o.delivery_status != 'Canceled' OR 1=1
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_30day_revenue():
    return fetch_data("""
        SELECT DATE(order_time) AS order_date,
               SUM(total_amount) AS daily_revenue
        FROM Orders
        WHERE order_time >= DATE('now','-30 days')
          AND delivery_status = 'Completed'
        GROUP BY DATE(order_time)
        ORDER BY order_date
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_campus_revenue():
    return fetch_data("""
        SELECT c.campus_id, c.name, c.real_location_lat, c.real_location_long,
               COALESCE(SUM(o.total_amount),0) AS revenue,
               COUNT(o.order_id) AS orders
        FROM Campuses c
        LEFT JOIN Stalls st ON c.campus_id = st.campus_id
        LEFT JOIN Orders o  ON st.stall_id = o.stall_id AND o.delivery_status='Completed'
        GROUP BY c.campus_id
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_wallet_ledger():
    return fetch_data("""
        SELECT wt.transaction_id, s.name AS student_name,
               s.email, wt.amount, wt.transaction_type,
               wt.timestamp
        FROM Wallet_Transactions wt
        JOIN Students s ON wt.student_id = s.student_id
        ORDER BY wt.timestamp DESC
        LIMIT 200
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_platform_settings():
    return fetch_data("SELECT setting_key, setting_value, description FROM Platform_Settings")

@st.cache_data(ttl=300, show_spinner=False)
def get_promotions():
    return fetch_data("""
        SELECT promo_code, discount_percentage, max_discount_amount, is_active
        FROM Promotions
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_category_by_campus():
    """Revenue breakdown by category and campus"""
    return fetch_data("""
        SELECT c.name AS campus,
               i.category,
               COALESCE(SUM(oi.unit_price * oi.quantity), 0) AS revenue,
               COUNT(DISTINCT o.order_id) AS orders
        FROM Campuses c
        LEFT JOIN Stalls st ON c.campus_id = st.campus_id
        LEFT JOIN Orders o ON st.stall_id = o.stall_id AND o.delivery_status = 'Completed'
        LEFT JOIN Order_Items oi ON o.order_id = oi.order_id
        LEFT JOIN Items i ON oi.item_id = i.item_id
        GROUP BY c.name, i.category
        ORDER BY campus, revenue DESC
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_top_stalls():
    """Top 15 performing stalls by revenue"""
    return fetch_data("""
        SELECT st.stall_id, st.name, 
               c.name AS campus,
               COALESCE(SUM(o.total_amount), 0) AS revenue,
               COUNT(o.order_id) AS orders,
               COALESCE(AVG(o.total_amount), 0) AS avg_order_value
        FROM Stalls st
        JOIN Campuses c ON st.campus_id = c.campus_id
        LEFT JOIN Orders o ON st.stall_id = o.stall_id AND o.delivery_status = 'Completed'
        GROUP BY st.stall_id
        ORDER BY revenue DESC
        LIMIT 15
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_order_type_breakdown():
    """Order type distribution (Pickup vs Delivery)"""
    return fetch_data("""
        SELECT order_type,
               COUNT(*) AS count,
               COALESCE(SUM(total_amount), 0) AS revenue,
               COALESCE(AVG(total_amount), 0) AS avg_value
        FROM Orders
        WHERE delivery_status = 'Completed'
        GROUP BY order_type
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_payment_breakdown():
    """Payment method preferences"""
    return fetch_data("""
        SELECT payment_method,
               COUNT(*) AS orders,
               COALESCE(SUM(total_amount), 0) AS revenue,
               COUNT(CASE WHEN payment_status = 'Paid' THEN 1 END) * 100.0 / COUNT(*) AS success_rate
        FROM Orders
        WHERE delivery_status = 'Completed'
        GROUP BY payment_method
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_aov_by_campus():
    """Average Order Value by Campus"""
    return fetch_data("""
        SELECT c.name AS campus,
               COUNT(o.order_id) AS total_orders,
               COALESCE(AVG(o.total_amount), 0) AS avg_order_value,
               COALESCE(SUM(o.total_amount), 0) AS total_revenue
        FROM Campuses c
        LEFT JOIN Stalls st ON c.campus_id = st.campus_id
        LEFT JOIN Orders o ON st.stall_id = o.stall_id AND o.delivery_status = 'Completed'
        GROUP BY c.campus_id, c.name
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_order_type_by_campus():
    """Order type distribution by campus"""
    return fetch_data("""
        SELECT c.name AS campus,
               o.order_type,
               COUNT(o.order_id) AS order_count
        FROM Campuses c
        LEFT JOIN Stalls st ON c.campus_id = st.campus_id
        LEFT JOIN Orders o ON st.stall_id = o.stall_id AND o.delivery_status = 'Completed'
        GROUP BY c.campus_id, c.name, o.order_type
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_cancellation_by_campus():
    """Cancellation rates by campus"""
    return fetch_data("""
        SELECT c.name AS campus,
               COUNT(CASE WHEN o.delivery_status = 'Canceled' THEN 1 END) * 100.0 / 
               NULLIF(COUNT(o.order_id), 0) AS cancel_rate,
               COUNT(o.order_id) AS total_orders,
               COUNT(CASE WHEN o.delivery_status = 'Canceled' THEN 1 END) AS canceled_orders
        FROM Campuses c
        LEFT JOIN Stalls st ON c.campus_id = st.campus_id
        LEFT JOIN Orders o ON st.stall_id = o.stall_id
        GROUP BY c.campus_id, c.name
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_peak_hours_by_campus():
    """Peak ordering hours by campus"""
    return fetch_data("""
        SELECT c.name AS campus,
               CAST(strftime('%H', o.order_time) AS INTEGER) AS hour,
               COUNT(o.order_id) AS order_count
        FROM Campuses c
        LEFT JOIN Stalls st ON c.campus_id = st.campus_id
        LEFT JOIN Orders o ON st.stall_id = o.stall_id AND o.delivery_status = 'Completed'
        GROUP BY c.campus_id, c.name, hour
        ORDER BY campus, hour
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_hourly_patterns():
    """Order patterns by hour of day"""
    return fetch_data("""
        SELECT CAST(STRFTIME('%H', order_time) AS INTEGER) AS hour,
               COUNT(*) AS orders,
               COALESCE(SUM(total_amount), 0) AS revenue
        FROM Orders
        WHERE delivery_status = 'Completed'
        GROUP BY hour
        ORDER BY hour
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_student_metrics():
    """Student engagement and lifetime value metrics"""
    return fetch_data("""
        SELECT 
            COUNT(DISTINCT s.student_id) AS total_students,
            COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN s.student_id END) AS active_students,
            COALESCE(AVG(student_lifetime_value.total), 0) AS avg_lifetime_value,
            COALESCE(MAX(student_lifetime_value.total), 0) AS highest_spender
        FROM Students s
        LEFT JOIN Orders o ON s.student_id = o.student_id AND o.delivery_status = 'Completed'
        LEFT JOIN (
            SELECT student_id, SUM(total_amount) AS total
            FROM Orders
            WHERE delivery_status = 'Completed'
            GROUP BY student_id
        ) student_lifetime_value ON s.student_id = student_lifetime_value.student_id
    """)

@st.cache_data(ttl=300, show_spinner=False)
def get_item_popularity():
    """Top 10 most ordered items"""
    return fetch_data("""
        SELECT i.name,
               i.category,
               COUNT(*) AS times_ordered,
               COALESCE(SUM(oi.quantity), 0) AS total_quantity,
               COALESCE(SUM(oi.unit_price * oi.quantity), 0) AS revenue
        FROM Order_Items oi
        JOIN Items i ON oi.item_id = i.item_id
        JOIN Orders o ON oi.order_id = o.order_id
        WHERE o.delivery_status = 'Completed'
        GROUP BY i.item_id
        ORDER BY times_ordered DESC
        LIMIT 10
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: COMMAND CENTER ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Command Center":
    st.title("📊 Global Command Center")
    st.caption("Real-time snapshot of the entire CampusEats platform.")

    kpi_df = get_platform_kpis()

    if not kpi_df.empty:
        kpi = kpi_df.iloc[0]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Total Platform Revenue",
                  f"PKR {kpi['total_revenue']:,.0f}",
                  delta=None)
        k2.metric("🎓 Active Students",
                  f"{kpi['active_students']:,}")
        k3.metric("🛒 Global Avg Order Value",
                  f"PKR {kpi['avg_order_value']:,.0f}")
        k4.metric("👛 Total Wallet Top-ups",
                  f"PKR {kpi['total_topups']:,.0f}")

    st.markdown("---")

    # ── 30-Day Revenue Line Chart ──────────────────────────────────────────────
    st.subheader("📈 30-Day Global Revenue Trend")
    rev_df = get_30day_revenue()
    if not rev_df.empty:
        rev_df["rolling_7d"] = rev_df["daily_revenue"].rolling(7, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=rev_df["order_date"], y=rev_df["daily_revenue"],
            name="Daily Revenue",
            line=dict(color=ORANGE, width=2),
            fill="tozeroy",
            fillcolor=f"rgba(255,107,53,0.12)",
            mode="lines",
        ))
        fig.add_trace(go.Scatter(
            x=rev_df["order_date"], y=rev_df["rolling_7d"],
            name="7-Day Rolling Avg",
            line=dict(color=GREEN, width=2.5, dash="dash"),
            mode="lines",
        ))
        fig.update_layout(
            xaxis_title="Date", yaxis_title="Revenue (PKR)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
        )
        st.plotly_chart(styled_chart(fig), use_container_width=True)
    else:
        st.info("📊 No order data available for the last 30 days.")

    st.markdown("---")
    
    # ── Hourly Order Patterns ──────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("⏰ Order Patterns by Hour")
        hourly_df = get_hourly_patterns()
        if not hourly_df.empty:
            fig_hourly = go.Figure()
            fig_hourly.add_trace(go.Bar(
                x=hourly_df["hour"].astype(str).str.zfill(2).add(":00"),
                y=hourly_df["orders"],
                name="Orders",
                marker_color=ORANGE,
                yaxis="y",
            ))
            fig_hourly.add_trace(go.Scatter(
                x=hourly_df["hour"].astype(str).str.zfill(2).add(":00"),
                y=hourly_df["revenue"],
                name="Revenue",
                line=dict(color=GREEN, width=2),
                yaxis="y2",
                mode="lines+markers",
            ))
            fig_hourly.update_layout(
                xaxis_title="Hour of Day",
                yaxis=dict(title="Order Count", side="left"),
                yaxis2=dict(title="Revenue (PKR)", overlaying="y", side="right"),
                hovermode="x unified",
                legend=dict(x=0.02, y=0.98),
            )
            st.plotly_chart(styled_chart(fig_hourly), use_container_width=True)
    
    with col2:
        st.subheader("👥 Student Metrics")
        student_df = get_student_metrics()
        if not student_df.empty:
            s = student_df.iloc[0]
            st.metric("Registered Students", f"{s['total_students']:,}")
            st.metric("Active Students", f"{s['active_students']:,}")
            st.metric("Avg Lifetime Value", f"PKR {s['avg_lifetime_value']:,.0f}")
            st.metric("Highest Spender", f"PKR {s['highest_spender']:,.0f}")

    st.markdown("---")
    
    # ── Order Type Distribution ────────────────────────────────────────────────
    st.subheader("📦 Order Type Distribution")
    order_type_df = get_order_type_breakdown()
    if not order_type_df.empty:
        fig_type = go.Figure(data=[go.Pie(
            labels=order_type_df["order_type"],
            values=order_type_df["count"],
            marker=dict(colors=[ORANGE, GREEN]),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Orders: %{value:,}<br>Revenue: PKR %{customdata:,.0f}<extra></extra>",
            customdata=order_type_df["revenue"],
        )])
        fig_type.update_layout(showlegend=True)
        st.plotly_chart(styled_chart(fig_type), use_container_width=True)

    st.markdown("---")
    
    # ── Payment Method Breakdown ───────────────────────────────────────────────
    st.subheader("💳 Payment Method Breakdown")
    payment_df = get_payment_breakdown()
    if not payment_df.empty:
        fig_payment = px.bar(
            payment_df, x="payment_method", y="revenue",
            color="payment_method",
            color_discrete_sequence=[ORANGE, GREEN],
            labels={"revenue": "Revenue (PKR)", "payment_method": "Payment Method"},
        )
        fig_payment.update_traces(text="", textposition="none")
        fig_payment.update_layout(coloraxis_showscale=False, showlegend=False)
        st.plotly_chart(styled_chart(fig_payment), use_container_width=True)
        
        # Add table with details
        with st.expander("📊 Payment Details"):
            payment_display = payment_df[["payment_method", "orders", "revenue", "success_rate"]].copy()
            payment_display["revenue"] = payment_display["revenue"].apply(lambda x: f"PKR {x:,.0f}")
            payment_display["success_rate"] = payment_display["success_rate"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                payment_display.rename(columns={
                    "payment_method": "Method",
                    "orders": "Orders",
                    "revenue": "Revenue",
                    "success_rate": "Success Rate"
                }),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")
    
    # ── Top Performing Stalls ──────────────────────────────────────────────────
    st.subheader("🏆 Top 10 Performing Stalls")
    top_stalls = get_top_stalls()
    if not top_stalls.empty:
        top_stalls_viz = top_stalls.head(10).sort_values("revenue")
        fig_stalls = px.bar(
            top_stalls_viz, x="revenue", y="name", orientation="h",
            color="revenue",
            color_continuous_scale=[[0, YELLOW], [1, ORANGE]],
            labels={"revenue": "Revenue (PKR)", "name": "Stall"},
        )
        fig_stalls.update_traces(text="", textposition="none")
        fig_stalls.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="Revenue (PKR)")
        st.plotly_chart(styled_chart(fig_stalls), use_container_width=True)
        
        # Add detailed table
        with st.expander("📋 Stall Details"):
            stall_display = top_stalls[["name", "campus", "orders", "revenue", "avg_order_value"]].copy()
            stall_display["revenue"] = stall_display["revenue"].apply(lambda x: f"PKR {x:,.0f}")
            stall_display["avg_order_value"] = stall_display["avg_order_value"].apply(lambda x: f"PKR {x:,.0f}")
            st.dataframe(
                stall_display.rename(columns={
                    "name": "Stall",
                    "campus": "Campus",
                    "orders": "Orders",
                    "revenue": "Revenue",
                    "avg_order_value": "Avg Value"
                }),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")
    
    # ── Most Popular Items ────────────────────────────────────────────────────
    st.subheader("🍽️ Most Popular Items")
    popular_items = get_item_popularity()
    if not popular_items.empty:
        popular_items_viz = popular_items.head(10).sort_values("times_ordered")
        fig_items = px.bar(
            popular_items_viz, x="times_ordered", y="name", orientation="h",
            color="revenue",
            color_continuous_scale=[[0, GREEN], [1, ORANGE]],
            labels={"times_ordered": "Times Ordered", "name": "Item"},
        )
        fig_items.update_traces(text="", textposition="none")
        fig_items.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="Times Ordered")
        st.plotly_chart(styled_chart(fig_items), use_container_width=True)
        
        # Add detailed table
        with st.expander("📋 Item Details"):
            items_display = popular_items[["name", "category", "times_ordered", "total_quantity", "revenue"]].copy()
            items_display["revenue"] = items_display["revenue"].apply(lambda x: f"PKR {x:,.0f}")
            st.dataframe(
                items_display.rename(columns={
                    "name": "Item",
                    "category": "Category",
                    "times_ordered": "Times Ordered",
                    "total_quantity": "Qty Sold",
                    "revenue": "Revenue"
                }),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")

    # ── Campus Folium Map (Bottom) ─────────────────────────────────────────────
    st.subheader("🗺️ Campus Locations — Pakistan")
    campus_df = get_campus_revenue()
    if not campus_df.empty:
        m = folium.Map(location=[30.5, 70.0], zoom_start=5,
                       tiles="CartoDB positron")
        max_rev = campus_df["revenue"].max() or 1
        for _, row in campus_df.iterrows():
            radius = 30_000 * (row["revenue"] / max_rev) + 15_000
            folium.CircleMarker(
                location=[row["real_location_lat"], row["real_location_long"]],
                radius=20,
                color=ORANGE, fill=True, fill_color=ORANGE, fill_opacity=0.55,
                popup=folium.Popup(
                    f"<b>{row['name']}</b><br>"
                    f"Revenue: PKR {row['revenue']:,.0f}<br>"
                    f"Orders: {row['orders']:,}",
                    max_width=220,
                ),
                tooltip=row["name"],
            ).add_to(m)
            folium.Circle(
                location=[row["real_location_lat"], row["real_location_long"]],
                radius=radius,
                color=ORANGE, fill=False, weight=1.5, opacity=0.4,
            ).add_to(m)
        st_folium(m, width="100%", height=420, returned_objects=[])


# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: CAMPUS SHOWDOWN ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Campus Showdown":
    st.title("🏆 Campus Showdown")
    st.caption("Head-to-head performance comparison across all three universities.")

    campus_df = get_campus_revenue()

    if not campus_df.empty:
        k1, k2, k3 = st.columns(3)
        cols = [k1, k2, k3]
        for i, row in campus_df.iterrows():
            cols[i].metric(f"🏫 {row['name']}",
                           f"PKR {row['revenue']:,.0f}",
                           f"{row['orders']:,} orders")

        st.markdown("---")

        # Daily orders per campus stacked bar
        st.subheader("📊 Daily Order Volumes by Campus")

        @st.cache_data(ttl=300, show_spinner=False)
        def get_daily_campus_orders():
            return fetch_data("""
                SELECT DATE(o.order_time) AS order_date,
                       c.name AS campus,
                       COUNT(o.order_id) AS order_count
                FROM Orders o
                JOIN Stalls st ON o.stall_id = st.stall_id
                JOIN Campuses c ON st.campus_id = c.campus_id
                WHERE o.order_time >= DATE('now','-30 days')
                GROUP BY order_date, c.name
                ORDER BY order_date
            """)

        daily_df = get_daily_campus_orders()
        if not daily_df.empty:
            fig_bar = px.bar(
                daily_df, x="order_date", y="order_count", color="campus",
                barmode="stack",
                color_discrete_sequence=[ORANGE, GREEN, YELLOW],
                labels={"order_date": "Date", "order_count": "Orders", "campus": "Campus"},
            )
            fig_bar.update_traces(text="", textposition="none")
            fig_bar.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(styled_chart(fig_bar), use_container_width=True)

        # Per-campus revenue bar
        st.subheader("💰 Revenue by Campus")
        fig_campus = px.bar(
            campus_df.sort_values("revenue", ascending=False),
            x="name", y="revenue", orientation="v",
            color="revenue",
            color_continuous_scale=[[0, "#FFC857"], [1, ORANGE]],
            labels={"revenue": "Total Revenue (PKR)", "name": "Campus"},
        )
        fig_campus.update_traces(text="", textposition="none")
        fig_campus.update_layout(
            coloraxis_showscale=False, xaxis_title="", yaxis_title="Revenue (PKR)",
        )
        st.plotly_chart(styled_chart(fig_campus), use_container_width=True)

        st.markdown("---")

        # Order Type Distribution by Campus
        st.subheader("📦 Order Type Distribution by Campus")
        order_type_df = get_order_type_by_campus()
        if not order_type_df.empty:
            fig_order_type = px.bar(
                order_type_df,
                x="order_count", y="campus", color="order_type", orientation="h",
                barmode="group",
                color_discrete_map={"Pickup": GREEN, "Delivery": ORANGE},
                labels={"order_count": "Orders", "campus": "Campus", "order_type": "Type"},
            )
            fig_order_type.update_traces(text="", textposition="none")
            fig_order_type.update_layout(
                hovermode="y unified",
                legend=dict(title="Order Type", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(styled_chart(fig_order_type), use_container_width=True)

        st.markdown("---")

        # Cancellation Rates by Campus
        st.subheader("🚫 Cancellation Rates by Campus")
        cancel_df = get_cancellation_by_campus()
        if not cancel_df.empty:
            fig_cancel = px.bar(
                cancel_df.sort_values("cancel_rate", ascending=False),
                x="campus", y="cancel_rate", orientation="v",
                color="cancel_rate",
                color_continuous_scale=[[0, GREEN], [1, RED]],
                labels={"cancel_rate": "Cancellation Rate (%)", "campus": "Campus"},
            )
            fig_cancel.update_traces(text="", textposition="none")
            fig_cancel.update_layout(
                coloraxis_showscale=False, xaxis_title="", yaxis_title="Cancellation Rate (%)",
            )
            st.plotly_chart(styled_chart(fig_cancel), use_container_width=True)

        st.markdown("---")

        # Peak Hours Heatmap by Campus
        st.subheader("⏰ Peak Ordering Hours by Campus")
        hours_df = get_peak_hours_by_campus()
        if not hours_df.empty:
            pivot_hours = hours_df.pivot_table(
                index="campus", columns="hour", values="order_count", fill_value=0
            )
            fig_heatmap = px.imshow(
                pivot_hours,
                labels=dict(x="Hour of Day", y="Campus", color="Orders"),
                color_continuous_scale="Viridis",
                aspect="auto",
            )
            fig_heatmap.update_xaxes(side="bottom")
            st.plotly_chart(styled_chart(fig_heatmap), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: PLATFORM ECONOMY ────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Platform Economy":
    st.title("💰 Platform Economy")
    st.caption("Category breakdown and key platform-wide performance indicators.")

    @st.cache_data(ttl=300, show_spinner=False)
    def get_category_revenue():
        return fetch_data("""
            SELECT i.category,
                   COALESCE(SUM(oi.unit_price * oi.quantity), 0) AS revenue,
                   COUNT(DISTINCT oi.order_id) AS orders
            FROM Order_Items oi
            JOIN Items i ON oi.item_id = i.item_id
            JOIN Orders o ON oi.order_id = o.order_id
            WHERE o.delivery_status = 'Completed'
            GROUP BY i.category
            ORDER BY revenue DESC
        """)

    @st.cache_data(ttl=300, show_spinner=False)
    def get_economy_kpis():
        return fetch_data("""
            SELECT
                SUM(CASE WHEN delivery_status='Canceled' THEN 1.0 ELSE 0 END)
                  / COUNT(*) * 100 AS cancel_rate,
                AVG(gst_amount)   AS avg_gst,
                SUM(tip_amount)   AS total_tips,
                SUM(discount_amount) AS total_discounts
            FROM Orders
        """)

    eco_df = get_economy_kpis()
    if not eco_df.empty:
        e = eco_df.iloc[0]
        
        # Row 1: Cancellation & GST
        k1, k2 = st.columns(2)
        k1.metric("❌ Cancellation Rate", f"{e['cancel_rate']:.1f}%", delta=None)
        k2.metric("🧾 Avg GST per Order", f"PKR {e['avg_gst']:,.0f}")
        
        st.markdown("---")
        
        # Row 2: Tips & Discounts
        k3, k4 = st.columns(2)
        k3.metric("💝 Total Tips Collected", f"PKR {e['total_tips']:,.0f}")
        k4.metric("🏷️ Total Discounts Given", f"PKR {e['total_discounts']:,.0f}")

    st.markdown("---")

    cat_df = get_category_revenue()
    if not cat_df.empty:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.subheader("🍽️ Revenue Share by Food Category")
            fig_donut = go.Figure(go.Pie(
                labels=cat_df["category"],
                values=cat_df["revenue"],
                hole=0.52,
                marker_colors=[ORANGE, GREEN, YELLOW, RED, "#9B59B6", "#3498DB", "#E74C3C"],
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Revenue: PKR %{value:,.0f}<extra></extra>",
            ))
            fig_donut.update_layout(
                showlegend=False,
            )
            st.plotly_chart(styled_chart(fig_donut), use_container_width=True)

        with col_right:
            st.subheader("📋 Category Details")
            cat_df["revenue_fmt"] = cat_df["revenue"].apply(lambda x: f"PKR {x:,.0f}")
            cat_df["orders_fmt"] = cat_df["orders"].astype(str)
            display_df = cat_df[["category", "revenue_fmt", "orders_fmt"]].rename(
                columns={"category": "Category", "revenue_fmt": "Revenue", "orders_fmt": "Orders"}
            ).sort_values("Revenue", ascending=False)
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")

    # ── Category Performance by Campus ─────────────────────────────────────────
    st.subheader("📊 Category Performance by Campus")
    cat_by_campus = get_category_by_campus()
    if not cat_by_campus.empty:
        # Pivot for better visualization
        pivot_df = cat_by_campus.pivot_table(
            index="category", columns="campus", values="revenue", fill_value=0
        )
        fig_campus_cat = px.bar(
            pivot_df, barmode="group",
            color_discrete_sequence=[ORANGE, GREEN, YELLOW],
            labels={"value": "Revenue (PKR)", "index": "Category"},
        )
        fig_campus_cat.update_traces(text="", textposition="none")
        fig_campus_cat.update_layout(
            xaxis_title="Category",
            yaxis_title="Revenue (PKR)",
            legend_title="Campus",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(styled_chart(fig_campus_cat), use_container_width=True)

    st.markdown("---")

    # ── Promotion Effectiveness ────────────────────────────────────────────────
    st.subheader("🏷️ Active Promotions")
    promo_df = get_promotions()
    if not promo_df.empty:
        promo_df["discount_percentage"] = promo_df["discount_percentage"].apply(
            lambda x: f"{x*100:.0f}%"
        )
        promo_df["max_discount_amount"] = promo_df["max_discount_amount"].apply(
            lambda x: f"PKR {x:,.0f}"
        )
        promo_df["Status"] = promo_df["is_active"].apply(
            lambda x: "✅ Active" if x else "❌ Disabled"
        )
        st.dataframe(
            promo_df.drop(columns=["is_active"]).rename(columns={
                "promo_code": "Code",
                "discount_percentage": "Discount %",
                "max_discount_amount": "Max Discount",
            }),
            use_container_width=True,
            hide_index=True,
        )



# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: SYSTEM MANAGEMENT ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ System Management":
    st.title("⚙️ System Management")
    st.caption("Update global settings, manage promotions, and audit wallet transactions.")

    # ── Platform Settings ──────────────────────────────────────────────────────
    with st.expander("🔧 Platform Settings", expanded=True):
        settings_df = get_platform_settings()
        if not settings_df.empty:
            for _, row in settings_df.iterrows():
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.text_input("Key", value=row["setting_key"],
                                disabled=True, key=f"skey_{row['setting_key']}")
                new_val = col2.text_input("Value", value=row["setting_value"],
                                          key=f"sval_{row['setting_key']}")
                if col3.button("💾 Save", key=f"sbtn_{row['setting_key']}"):
                    ok = execute_write(
                        "UPDATE Platform_Settings SET setting_value = :v WHERE setting_key = :k",
                        {"v": new_val, "k": row["setting_key"]},
                    )
                    if ok:
                        st.success(f"✅ `{row['setting_key']}` updated to `{new_val}`")
                        fetch_data.clear()
                        get_platform_settings.clear()
                        st.rerun()
                st.caption(row.get("description", ""))

    st.markdown("---")

    # ── Promotions Management ──────────────────────────────────────────────────
    with st.expander("🏷️ Promotions Management", expanded=False):
        promo_df = get_promotions()
        if not promo_df.empty:
            for _, row in promo_df.iterrows():
                c1, c2 = st.columns([3, 1])
                status = "✅ Active" if row["is_active"] else "❌ Disabled"
                c1.markdown(
                    f"**{row['promo_code']}** — {row['discount_percentage']*100:.0f}% off "
                    f"(max PKR {row['max_discount_amount']:,.0f})  {status}"
                )
                toggle_label = "Disable" if row["is_active"] else "Enable"
                if c2.button(toggle_label, key=f"promo_{row['promo_code']}"):
                    execute_write(
                        "UPDATE Promotions SET is_active = :v WHERE promo_code = :c",
                        {"v": 0 if row["is_active"] else 1, "c": row["promo_code"]},
                    )
                    fetch_data.clear()
                    get_promotions.clear()
                    st.rerun()

        st.markdown("##### ➕ Add New Promotion")
        with st.form("add_promo"):
            pc = st.text_input("Promo Code (e.g. BIRYANI20)")
            pct = st.number_input("Discount %", min_value=1, max_value=100, value=10)
            max_disc = st.number_input("Max Discount (PKR)", min_value=10, value=500)
            if st.form_submit_button("Add Promo", type="primary"):
                if pc:
                    execute_write(
                        """INSERT INTO Promotions (promo_code, discount_percentage,
                           max_discount_amount, is_active)
                           VALUES (:c, :p, :m, 1)""",
                        {"c": pc.upper(), "p": pct / 100, "m": max_disc},
                    )
                    fetch_data.clear()
                    get_promotions.clear()
                    st.success(f"Promo **{pc.upper()}** added.")
                    st.rerun()

    st.markdown("---")

    # ── Wallet Ledger ─────────────────────────────────────────────────────────
    with st.expander("👛 Wallet Transaction Ledger (Last 200)", expanded=False):
        ledger_df = get_wallet_ledger()
        if not ledger_df.empty:
            def colour_amount(val):
                colour = GREEN if val > 0 else RED
                return f"color: {colour}"

            styled = (
                ledger_df.style
                .map(colour_amount, subset=["amount"])
                .format({"amount": "PKR {:.2f}"})
            )
            st.dataframe(styled, use_container_width=True, hide_index=True,
                         height=400)
