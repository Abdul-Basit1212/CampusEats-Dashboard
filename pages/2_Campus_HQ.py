"""
pages/2_📍_Campus_HQ.py — CampusEats Dashboard
Campus Incharge (or Admin with campus selector) View.
Access: admin | incharge
Scoping: All queries parameterised with campus_id.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from database import fetch_data, get_all_campuses

# ── Page config & auth guard ──────────────────────────────────────────────────
st.set_page_config(page_title="Campus HQ · CampusEats", page_icon="📍", layout="wide")

if not st.session_state.get("logged_in"):
    st.switch_page("Home.py")
if st.session_state.user_role not in ("admin", "incharge"):
    st.error("🚫 Access denied.")
    st.stop()

# ── Brand colours ─────────────────────────────────────────────────────────────
ORANGE = "#FF6B35"
GREEN  = "#2EC4B6"
RED    = "#E71D36"
YELLOW = "#FFC857"

# ── Theme detection & chart styling ────────────────────────────────────────────
def get_chart_template():
    """Get Plotly template based on Streamlit theme"""
    try:
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

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📍 Campus HQ")
    st.divider()
    st.markdown(f"### 👋 {st.session_state.user_name}")
    role_label = "🌍 Global Admin" if st.session_state.user_role == "admin" else "📍 Campus Incharge"
    st.markdown(f"**Role:** {role_label}")
    st.divider()
    page = st.radio(
        "Navigate",
        ["🏠 Campus HQ", "🏆 Stall Leaderboard", "🚨 Intervention Center"],
        label_visibility="collapsed",
    )
    st.divider()
    
    # Campus Selector
    if st.session_state.user_role == "admin":
        campuses_df = get_all_campuses()
        campus_options = {row["name"]: row["campus_id"] for _, row in campuses_df.iterrows()}
        selected_campus_name = st.selectbox(
            "🏫 Select Campus", list(campus_options.keys())
        )
        active_campus_id = campus_options[selected_campus_name]
    else:
        active_campus_id = int(st.session_state.campus_id)
        campuses_df = get_all_campuses()
        selected_campus_name = campuses_df.loc[
            campuses_df["campus_id"] == active_campus_id, "name"
        ].values[0] if not campuses_df.empty else "Campus"
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("Home.py")

# ═══════════════════════════════════════════════════════════════════════════════
# ── DATA FETCHERS (all scoped to campus_id) ───────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_campus_kpis(campus_id: int):
    return fetch_data("""
        SELECT
            COALESCE(SUM(CASE WHEN DATE(o.order_time)=DATE('now')
                         THEN o.total_amount ELSE 0 END), 0) AS today_revenue,
            COUNT(DISTINCT CASE WHEN DATE(o.order_time)=DATE('now')
                           THEN o.order_id END)              AS today_orders,
            COUNT(DISTINCT st.stall_id)                      AS active_stalls,
            (SELECT COUNT(*) FROM Riders r
             WHERE r.campus_id=:cid
               AND r.current_status='Available'
               AND r.is_active=1)                            AS available_riders,
            COALESCE(
              SUM(CASE WHEN o.delivery_status='Completed' THEN 1.0 ELSE 0 END)
              / NULLIF(COUNT(o.order_id),0) * 100, 0)        AS completion_rate
        FROM Stalls st
        LEFT JOIN Orders o ON st.stall_id = o.stall_id
        WHERE st.campus_id = :cid
          AND st.is_active = 1
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_stall_leaderboard(campus_id: int):
    return fetch_data("""
        SELECT st.stall_id, st.name AS stall_name, st.category,
               COALESCE(SUM(o.total_amount),0)  AS total_revenue,
               COUNT(o.order_id)                AS total_orders,
               COALESCE(AVG(r.rating),0)        AS avg_rating
        FROM Stalls st
        LEFT JOIN Orders o  ON st.stall_id = o.stall_id
                           AND o.delivery_status='Completed'
        LEFT JOIN Reviews r ON o.order_id = r.order_id
        WHERE st.campus_id = :cid
          AND st.is_active = 1
        GROUP BY st.stall_id, st.name, st.category
        ORDER BY total_revenue DESC
    """, {"cid": campus_id})

@st.cache_data(ttl=120, show_spinner=False)
def get_canceled_orders(campus_id: int):
    return fetch_data("""
        SELECT o.order_id, s.name AS student_name,
               st.name AS stall_name, o.order_time,
               o.total_amount, o.cancel_reason
        FROM Orders o
        JOIN Students s ON o.student_id = s.student_id
        JOIN Stalls st  ON o.stall_id   = st.stall_id
        WHERE st.campus_id = :cid
          AND o.delivery_status = 'Canceled'
        ORDER BY o.order_time DESC
        LIMIT 100
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_quality_watchlist(campus_id: int):
    """Stalls whose 7-day average rating is below 3.0."""
    return fetch_data("""
        SELECT st.stall_id, st.name AS stall_name, st.category,
               ROUND(AVG(r.rating), 2) AS avg_rating_7d,
               COUNT(r.review_id) AS review_count
        FROM Stalls st
        JOIN Orders o  ON st.stall_id = o.stall_id
                       AND o.order_time >= DATE('now','-7 days')
        JOIN Reviews r ON o.order_id = r.order_id
        WHERE st.campus_id = :cid
        GROUP BY st.stall_id, st.name, st.category
        HAVING avg_rating_7d < 3.0
        ORDER BY avg_rating_7d ASC
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_campus_stall_locations(campus_id: int):
    return fetch_data("""
        SELECT st.stall_id, st.name, st.category,
               st.location_lat, st.location_long,
               COALESCE(SUM(o.total_amount),0) AS revenue
        FROM Stalls st
        LEFT JOIN Orders o ON st.stall_id = o.stall_id
                          AND o.delivery_status = 'Completed'
        WHERE st.campus_id = :cid AND st.is_active = 1
          AND st.location_lat IS NOT NULL
        GROUP BY st.stall_id
    """, {"cid": campus_id})

@st.cache_data(ttl=60, show_spinner=False)
def get_active_riders(campus_id: int):
    return fetch_data("""
        SELECT rider_id, name, current_status,
               location_lat, location_long, vehicle_type
        FROM Riders
        WHERE campus_id = :cid AND is_active = 1
          AND location_lat IS NOT NULL
        LIMIT 50
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_revenue_trend_30d(campus_id: int):
    """30-day revenue trend"""
    return fetch_data("""
        SELECT DATE(o.order_time) AS order_date,
               SUM(o.total_amount) AS daily_revenue,
               COUNT(o.order_id) AS daily_orders
        FROM Orders o
        JOIN Stalls st ON o.stall_id = st.stall_id
        WHERE st.campus_id = :cid
          AND o.delivery_status = 'Completed'
          AND o.order_time >= DATE('now','-30 days')
        GROUP BY DATE(o.order_time)
        ORDER BY order_date
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_category_breakdown(campus_id: int):
    """Revenue and orders by food category"""
    return fetch_data("""
        SELECT i.category,
               COUNT(DISTINCT o.order_id) AS order_count,
               COALESCE(SUM(o.total_amount), 0) AS revenue
        FROM Orders o
        JOIN Order_Items oi ON o.order_id = oi.order_id
        JOIN Items i ON oi.item_id = i.item_id
        JOIN Stalls st ON o.stall_id = st.stall_id
        WHERE st.campus_id = :cid AND o.delivery_status = 'Completed'
        GROUP BY i.category
        ORDER BY revenue DESC
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_payment_breakdown(campus_id: int):
    """Payment method distribution"""
    return fetch_data("""
        SELECT o.payment_method,
               COUNT(o.order_id) AS order_count,
               COALESCE(SUM(o.total_amount), 0) AS revenue
        FROM Orders o
        JOIN Stalls st ON o.stall_id = st.stall_id
        WHERE st.campus_id = :cid AND o.delivery_status = 'Completed'
        GROUP BY o.payment_method
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_hourly_patterns(campus_id: int):
    """Orders by hour of day"""
    return fetch_data("""
        SELECT CAST(strftime('%H', o.order_time) AS INTEGER) AS hour,
               COUNT(o.order_id) AS order_count,
               COALESCE(SUM(o.total_amount), 0) AS revenue
        FROM Orders o
        JOIN Stalls st ON o.stall_id = st.stall_id
        WHERE st.campus_id = :cid AND o.delivery_status = 'Completed'
        GROUP BY hour
        ORDER BY hour
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_top_students(campus_id: int):
    """Top student spenders on campus"""
    return fetch_data("""
        SELECT s.name AS student_name,
               COUNT(o.order_id) AS order_count,
               COALESCE(SUM(o.total_amount), 0) AS total_spent
        FROM Orders o
        JOIN Students s ON o.student_id = s.student_id
        JOIN Stalls st ON o.stall_id = st.stall_id
        WHERE st.campus_id = :cid AND o.delivery_status = 'Completed'
        GROUP BY s.student_id, s.name
        ORDER BY total_spent DESC
        LIMIT 10
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_rider_performance(campus_id: int):
    """Delivery partner performance metrics"""
    return fetch_data("""
        SELECT r.name AS rider_name,
               COUNT(o.order_id) AS deliveries,
               COALESCE(AVG(o.tip_amount), 0) AS avg_tip,
               COUNT(CASE WHEN o.delivery_status = 'Completed' THEN 1 END) * 100.0 /
               NULLIF(COUNT(o.order_id), 0) AS completion_rate
        FROM Riders r
        LEFT JOIN Orders o ON r.rider_id = o.rider_id
        WHERE r.campus_id = :cid AND r.is_active = 1
        GROUP BY r.rider_id, r.name
        ORDER BY deliveries DESC
        LIMIT 10
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_stall_order_trend_30d(campus_id: int, stall_id: int):
    """30-day order trend for a single stall"""
    return fetch_data("""
        SELECT DATE(o.order_time) AS order_date,
               COUNT(o.order_id) AS order_count,
               SUM(o.total_amount) AS daily_revenue
        FROM Orders o
        JOIN Stalls st ON o.stall_id = st.stall_id
        WHERE st.campus_id = :cid AND st.stall_id = :sid
          AND o.delivery_status = 'Completed'
          AND o.order_time >= DATE('now','-30 days')
        GROUP BY DATE(o.order_time)
        ORDER BY order_date
    """, {"cid": campus_id, "sid": stall_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_stall_category_performance(campus_id: int):
    """Category performance across all stalls"""
    return fetch_data("""
        SELECT i.category,
               COUNT(DISTINCT o.order_id) AS orders,
               SUM(o.total_amount) AS revenue,
               AVG(r.rating) AS avg_rating
        FROM Orders o
        JOIN Order_Items oi ON o.order_id = oi.order_id
        JOIN Items i ON oi.item_id = i.item_id
        JOIN Stalls st ON o.stall_id = st.stall_id
        LEFT JOIN Reviews r ON o.order_id = r.order_id
        WHERE st.campus_id = :cid AND o.delivery_status = 'Completed'
        GROUP BY i.category
        ORDER BY revenue DESC
    """, {"cid": campus_id})

@st.cache_data(ttl=300, show_spinner=False)
def get_poor_performing_stalls(campus_id: int):
    """Stalls with low completion rates or high cancellations"""
    return fetch_data("""
        SELECT st.stall_id, st.name AS stall_name,
               COUNT(CASE WHEN o.delivery_status = 'Completed' THEN 1 END) * 100.0 /
               NULLIF(COUNT(o.order_id), 0) AS completion_rate,
               COUNT(CASE WHEN o.delivery_status = 'Canceled' THEN 1 END) AS canceled_count,
               COUNT(o.order_id) AS total_orders
        FROM Stalls st
        LEFT JOIN Orders o ON st.stall_id = o.stall_id
        WHERE st.campus_id = :cid AND st.is_active = 1
        GROUP BY st.stall_id, st.name
        HAVING completion_rate < 80 AND canceled_count > 5
        ORDER BY completion_rate ASC
    """, {"cid": campus_id})

# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: CAMPUS HQ ──────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Campus HQ":
    st.title(f"🏠 {selected_campus_name} — Campus HQ")
    st.caption("Live operational overview for this campus.")

    kpi_df = get_campus_kpis(active_campus_id)
    if not kpi_df.empty:
        k = kpi_df.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Today's Revenue", f"PKR {k['today_revenue']:,.0f}")
        col2.metric("📦 Today's Orders", f"{int(k['today_orders'] or 0):,}")
        col3.metric("🍽️ Active Stalls", f"{int(k['active_stalls'] or 0)}")
        col4.metric("🛵 Available Riders", f"{int(k['available_riders'] or 0)}")

    st.markdown("---")

    # ── Section 1: Revenue Trend ──────────────────────────────────────────────
    st.subheader("📈 30-Day Revenue Trend")
    trend_df = get_revenue_trend_30d(active_campus_id)
    if not trend_df.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=trend_df["order_date"], y=trend_df["daily_revenue"],
            name="Daily Revenue", marker_color=ORANGE, opacity=0.75,
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend_df["order_date"],
            y=trend_df["daily_revenue"].rolling(7, min_periods=1).mean(),
            name="7-Day Avg", line=dict(color=GREEN, width=2.5, dash="dash"),
            mode="lines",
        ))
        fig_trend.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(styled_chart(fig_trend), use_container_width=True)

    st.markdown("---")

    # ── Section 2: Category & Payment Breakdown ───────────────────────────────
    st.subheader("🍽️ Revenue by Category & 💳 Payment Methods")
    col_cat, col_pay = st.columns(2)

    with col_cat:
        cat_df = get_category_breakdown(active_campus_id)
        if not cat_df.empty:
            fig_cat = px.pie(
                cat_df, values="revenue", names="category",
                hole=0.4,
                color_discrete_sequence=[ORANGE, GREEN, YELLOW, RED, "#9B59B6", "#3498DB"],
            )
            fig_cat.update_traces(textinfo="label+percent")
            st.plotly_chart(styled_chart(fig_cat), use_container_width=True)

    with col_pay:
        pay_df = get_payment_breakdown(active_campus_id)
        if not pay_df.empty:
            fig_pay = px.bar(
                pay_df.sort_values("revenue", ascending=True),
                x="revenue", y="payment_method", orientation="h",
                color="revenue",
                color_continuous_scale=[[0, YELLOW], [1, GREEN]],
                labels={"revenue": "Revenue (PKR)", "payment_method": "Method"},
            )
            fig_pay.update_traces(text="", textposition="none")
            fig_pay.update_layout(coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(styled_chart(fig_pay), use_container_width=True)

    st.markdown("---")

    # ── Section 3: Hourly Patterns ───────────────────────────────────────────
    st.subheader("⏰ Peak Order Hours")
    hours_df = get_hourly_patterns(active_campus_id)
    if not hours_df.empty:
        fig_hours = px.line(
            hours_df, x="hour", y="order_count",
            markers=True,
        )
        fig_hours.update_xaxes(tickmode="linear", tick0=0, dtick=1)
        st.plotly_chart(styled_chart(fig_hours), use_container_width=True)

    st.markdown("---")

    # ── Section 4: Top Delivery Partners ─────────────────────────────────────
    st.subheader("🛵 Top Delivery Partners")
    rider_df = get_rider_performance(active_campus_id)
    if not rider_df.empty:
        rider_df["completion_rate"] = rider_df["completion_rate"].fillna(0)
        rider_df["avg_tip"] = rider_df["avg_tip"].apply(lambda x: f"PKR {x:.0f}")
        display_df = rider_df[["rider_name", "deliveries", "completion_rate", "avg_tip"]].rename(
            columns={"rider_name": "Rider", "deliveries": "Deliveries", 
                     "completion_rate": "Completion %", "avg_tip": "Avg Tip"}
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Section 5: Top Student Spenders ──────────────────────────────────────
    st.subheader("👥 Top Student Spenders")
    student_df = get_top_students(active_campus_id)
    if not student_df.empty:
        student_df["total_spent"] = student_df["total_spent"].apply(lambda x: f"PKR {x:,.0f}")
        display_df = student_df[["student_name", "order_count", "total_spent"]].rename(
            columns={"student_name": "Student", "order_count": "Orders", "total_spent": "Total Spent"}
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Section 6: Live Campus Map ────────────────────────────────────────────
    st.subheader("🗺️ Live Campus Map")
    campuses_df2 = get_all_campuses()
    campus_row = campuses_df2[campuses_df2["campus_id"] == active_campus_id]
    if not campus_row.empty:
        lat = campus_row.iloc[0]["real_location_lat"]
        lon = campus_row.iloc[0]["real_location_long"]
        m = folium.Map(location=[lat, lon], zoom_start=15,
                       tiles="CartoDB positron")

        # Stall markers
        stall_locs = get_campus_stall_locations(active_campus_id)
        for _, row in stall_locs.iterrows():
            folium.CircleMarker(
                location=[row["location_lat"], row["location_long"]],
                radius=8,
                color=ORANGE, fill=True, fill_color=ORANGE, fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>{row['name']}</b><br>{row['category']}<br>"
                    f"Revenue: PKR {row['revenue']:,.0f}",
                    max_width=180,
                ),
                tooltip=row["name"],
            ).add_to(m)

        # Rider markers (increased to show more riders)
        riders = get_active_riders(active_campus_id)
        for _, r in riders.iterrows():
            colour = GREEN if r["current_status"] == "Available" else YELLOW
            folium.Marker(
                location=[r["location_lat"], r["location_long"]],
                icon=folium.Icon(color="green" if r["current_status"] == "Available" else "orange",
                                 icon="bicycle", prefix="fa"),
                tooltip=f"Rider: {r['name']} ({r['current_status']})",
            ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width="100%", height=440, returned_objects=[], key=f"campus_map_{active_campus_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: STALL LEADERBOARD ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Stall Leaderboard":
    st.title(f"🏆 {selected_campus_name} — Stall Leaderboard")

    lb_df = get_stall_leaderboard(active_campus_id)

    if not lb_df.empty:
        # Category filter
        cats = ["All"] + sorted(lb_df["category"].unique().tolist())
        selected_cats = st.multiselect(
            "🔍 Filter by Category", cats[1:], default=[],
            placeholder="All categories shown"
        )
        filtered = lb_df if not selected_cats else lb_df[lb_df["category"].isin(selected_cats)]

        # ── Section 1: Revenue & Rating Charts ────────────────────────────────
        st.subheader("💰 Highest Grossing Stalls & ⭐ Highest Rated Stalls")
        col_l, col_r = st.columns(2)

        with col_l:
            top_rev = filtered.nlargest(15, "total_revenue")
            fig_rev = px.bar(
                top_rev.sort_values("total_revenue"),
                x="total_revenue", y="stall_name", orientation="h",
                color="total_revenue",
                color_continuous_scale=[[0, YELLOW], [1, ORANGE]],
                labels={"total_revenue": "Revenue (PKR)", "stall_name": "Stall"},
            )
            fig_rev.update_traces(text="", textposition="none")
            fig_rev.update_layout(coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(styled_chart(fig_rev), use_container_width=True)

        with col_r:
            has_ratings = filtered[filtered["avg_rating"] > 0]
            if not has_ratings.empty:
                top_rated = has_ratings.nlargest(15, "avg_rating")
                fig_rat = px.bar(
                    top_rated.sort_values("avg_rating"),
                    x="avg_rating", y="stall_name", orientation="h",
                    color="avg_rating",
                    color_continuous_scale=[[0, GREEN], [1, YELLOW]],
                    labels={"avg_rating": "Avg Rating", "stall_name": "Stall"},
                    range_x=[0, 5],
                )
                fig_rat.update_traces(text="", textposition="none")
                fig_rat.update_layout(coloraxis_showscale=False, yaxis_title="")
                st.plotly_chart(styled_chart(fig_rat), use_container_width=True)
            else:
                st.info("No ratings data available yet.")

        st.markdown("---")

        # ── Section 2: Category Performance ───────────────────────────────────
        st.subheader("🍽️ Category Performance Across Stalls")
        cat_perf = get_stall_category_performance(active_campus_id)
        if not cat_perf.empty:
            cat_perf["avg_rating"] = cat_perf["avg_rating"].fillna(0)
            col_cat1, col_cat2 = st.columns(2)

            with col_cat1:
                fig_cat_rev = px.bar(
                    cat_perf.sort_values("revenue"),
                    x="revenue", y="category", orientation="h",
                    color="revenue",
                    color_continuous_scale=[[0, YELLOW], [1, ORANGE]],
                    labels={"revenue": "Revenue (PKR)", "category": "Category"},
                )
                fig_cat_rev.update_traces(text="", textposition="none")
                fig_cat_rev.update_layout(coloraxis_showscale=False, yaxis_title="")
                st.plotly_chart(styled_chart(fig_cat_rev), use_container_width=True)

            with col_cat2:
                fig_cat_rate = px.bar(
                    cat_perf.sort_values("avg_rating"),
                    x="avg_rating", y="category", orientation="h",
                    color="avg_rating",
                    color_continuous_scale=[[0, RED], [1, GREEN]],
                    labels={"avg_rating": "Avg Rating", "category": "Category"},
                )
                fig_cat_rate.update_traces(text="", textposition="none")
                fig_cat_rate.update_layout(coloraxis_showscale=False, yaxis_title="")
                st.plotly_chart(styled_chart(fig_cat_rate), use_container_width=True)

        st.markdown("---")

        # ── Section 3: Full Stall Rankings Table ──────────────────────────────
        st.subheader("📋 Full Stall Rankings")
        display_df = filtered[["stall_name", "category", "total_revenue",
                                "total_orders", "avg_rating"]].copy()
        display_df["total_revenue"] = display_df["total_revenue"].apply(lambda x: f"PKR {x:,.0f}")
        display_df["avg_rating"] = display_df["avg_rating"].apply(
            lambda x: f"⭐ {x:.2f}" if x > 0 else "—"
        )
        display_df.columns = ["Stall", "Category", "Revenue", "Orders", "Rating"]
        display_df = display_df.reset_index(drop=True)
        display_df.index += 1
        st.dataframe(display_df, use_container_width=True, height=400)

        st.markdown("---")

        # ── Section 4: Poor Performing Stalls ────────────────────────────────
        st.subheader("⚠️ Performance Alerts")
        poor_stalls = get_poor_performing_stalls(active_campus_id)
        if not poor_stalls.empty:
            st.warning(f"🚨 {len(poor_stalls)} stall(s) need attention (completion rate <80% or >5 cancellations)")
            poor_stalls["completion_rate"] = poor_stalls["completion_rate"].fillna(0)
            display_poor = poor_stalls[["stall_name", "completion_rate", "canceled_count", "total_orders"]].copy()
            display_poor["completion_rate"] = display_poor["completion_rate"].apply(lambda x: f"{x:.1f}%")
            display_poor.columns = ["Stall", "Completion Rate", "Canceled", "Total Orders"]
            st.dataframe(display_poor, use_container_width=True, hide_index=True)
        else:
            st.success("✅ All stalls performing well!")
    else:
        st.info("No stall data found for this campus.")


# ═══════════════════════════════════════════════════════════════════════════════
# ── PAGE: INTERVENTION CENTER ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🚨 Intervention Center":
    st.title(f"🚨 {selected_campus_name} — Intervention Center")
    st.caption("Quality watchlist and live cancellation feed to keep the campus running smoothly.")

    # ── Section 1: Cancellation Feed ──────────────────────────────────────────
    st.subheader("❌ Cancellation Feed")
    canceled_df = get_canceled_orders(active_campus_id)
    
    # Group cancel reasons for a quick summary
    reason_counts = canceled_df["cancel_reason"].value_counts().reset_index() if not canceled_df.empty else pd.DataFrame()
    
    if not reason_counts.empty:
        reason_counts.columns = ["Reason", "Count"]

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.metric("Total Canceled Orders (All Time)", f"{len(canceled_df):,}")
    with col_r:
        top_reason = reason_counts.iloc[0]["Reason"] if not reason_counts.empty else "N/A"
        st.metric("Top Cancel Reason", top_reason)

    if not reason_counts.empty:
        fig_reasons = px.bar(
            reason_counts.head(8),
            x="Count", y="Reason", orientation="h",
            color="Count",
            color_continuous_scale=[[0, "#FDECEA"], [1, RED]],
            labels={"Count": "Occurrences", "Reason": "Cancel Reason"},
        )
        fig_reasons.update_traces(text="", textposition="none")
        fig_reasons.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(styled_chart(fig_reasons), use_container_width=True)
    else:
        st.info("No cancellations recorded yet for this campus.")

    st.markdown("---")

    # ── Section 2: Canceled Orders Table ──────────────────────────────────────
    st.subheader("📋 Recent Canceled Orders")
    if not canceled_df.empty:
        st.dataframe(
            canceled_df.rename(columns={
                "order_id": "Order ID", "student_name": "Student",
                "stall_name": "Stall", "order_time": "Time",
                "total_amount": "Amount (PKR)", "cancel_reason": "Reason",
            }),
            use_container_width=True,
            height=320,
            hide_index=True,
        )
    else:
        st.success("🎉 No canceled orders recorded for this campus!")

    st.markdown("---")

    # ── Section 3: Quality Watchlist ──────────────────────────────────────────
    st.subheader("⚠️ Quality Watchlist (7-Day Avg Rating < 3.0)")
    watchlist_df = get_quality_watchlist(active_campus_id)
    if not watchlist_df.empty:
        st.warning(f"🚨 {len(watchlist_df)} stall(s) flagged for low ratings in the last 7 days.")
        
        # Show chart of low-rated stalls
        watchlist_sorted = watchlist_df.sort_values("avg_rating_7d")
        fig_watch = px.bar(
            watchlist_sorted,
            x="avg_rating_7d", y="stall_name", orientation="h",
            color="avg_rating_7d",
            color_continuous_scale=[[0, RED], [1, YELLOW]],
            labels={"avg_rating_7d": "7d Avg Rating", "stall_name": "Stall"},
        )
        fig_watch.update_traces(text="", textposition="none")
        fig_watch.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(styled_chart(fig_watch), use_container_width=True)

        st.markdown("---")

        st.subheader("📊 Watchlist Details")
        watchlist_df["avg_rating_7d"] = watchlist_df["avg_rating_7d"].apply(
            lambda x: f"⭐ {x:.2f}"
        )
        st.dataframe(
            watchlist_df.rename(columns={
                "stall_id": "Stall ID", "stall_name": "Stall Name",
                "category": "Category", "avg_rating_7d": "7d Avg Rating",
                "review_count": "Reviews",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("✅ All stalls are performing well (7-day avg rating ≥ 3.0).")
