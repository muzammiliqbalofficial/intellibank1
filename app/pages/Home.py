import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.utils.session import require_auth
from app.utils.data_store import get_dataset, is_data_loaded, get_summary, get_branch_df, get_revenue_df
from app.components.theme import load_css, apply_theme, render_page_header, metric_card, render_footer
from app.components.sidebar import render_sidebar
from app.components.tour import render_tour

st.set_page_config(page_title="IntelliBank — Dashboard", page_icon="🏦",
                   layout="wide", initial_sidebar_state="expanded")
load_css()
user = require_auth()
apply_theme(st.session_state.get("theme", "light"))
render_sidebar()
render_tour()

role = user.get("role", "business_analyst")
df      = get_dataset()
loaded  = is_data_loaded()
summary = get_summary()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD — User management & system logs
# ══════════════════════════════════════════════════════════════════════════════
if role == "admin":
    render_page_header("Admin Dashboard", "User management and system activity overview", "🔐")

    from app.utils.session import get_db_session
    db = get_db_session()
    try:
        from db.models import User, AuditLog
        users    = db.query(User).all()
        logs     = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all() \
                   if hasattr(AuditLog, "created_at") else []
    except Exception:
        users, logs = [], []
    finally:
        db.close()

    # KPIs
    c1, c2, c3 = st.columns(3)
    role_counts = {}
    for u in users:
        role_counts[u.role] = role_counts.get(u.role, 0) + 1

    with c1: metric_card("Total Users",        str(len(users)),                          "👥")
    with c2: metric_card("Bank Managers",      str(role_counts.get("bank_manager", 0)),  "🟡")
    with c3: metric_card("Business Analysts",  str(role_counts.get("business_analyst", 0)), "🟢")

    st.markdown("<br/>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("Registered Users")
        if users:
            user_data = [{
                "Username":  u.username,
                "Full Name": u.full_name,
                "Role":      u.role,
                "Email":     u.email,
            } for u in users]
            st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)
        else:
            st.info("No users found.")

    with col_r:
        st.subheader("Role Distribution")
        if role_counts:
            fig = go.Figure(go.Pie(
                labels=list(role_counts.keys()),
                values=list(role_counts.values()),
                marker=dict(colors=["#c62828", "#f9a825", "#1a237e"]),
                hole=0.45, textinfo="percent+label",
            ))
            fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
                              paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Recent Activity Logs")
    if logs:
        log_data = [{
            "Action":    l.action,
            "User":      l.username if hasattr(l, "username") else str(l.user_id),
            "Timestamp": str(l.created_at)[:16] if l.created_at else "",
        } for l in logs]
        st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
    else:
        st.info("No activity logs yet.")

    render_footer()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# BANK MANAGER — Executive Dashboard (Revenue + Branch)
# ══════════════════════════════════════════════════════════════════════════════
elif role == "bank_manager":
    render_page_header("Executive Dashboard", "Strategic overview — Revenue & Branch performance", "📊")

    if not loaded:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px;">
            <div style="font-size:4rem; margin-bottom:16px;">📤</div>
            <h2 style="color:#1a237e;">No Data Uploaded Yet</h2>
            <p style="color:#9e9e9e;">Upload your banking dataset to see real insights here.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Data Upload →", type="primary"):
            st.switch_page("pages/Data_Upload.py")
        render_footer()
        st.stop()

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Revenue",
                         f"₨{summary.get('total_revenue',0)/1e6:.1f}M", "💰")
    with c2: metric_card("Total Transactions",
                         f"{summary.get('total_rows',0):,}", "💳")
    with c3: metric_card("Active Branches",
                         f"{summary.get('total_branches',0)}", "🏢")
    with c4: metric_card("Top Branch",
                         summary.get('top_branch','—'), "🏆")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Revenue over time
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.subheader("Revenue Over Time")
        rev_df = get_revenue_df()
        if not rev_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=rev_df["date"], y=rev_df["revenue"],
                name="Daily Revenue", fill="tozeroy",
                line=dict(color="#1a237e", width=2),
                fillcolor="rgba(26,35,126,0.08)"
            ))
            # 7-day rolling avg
            rev_df["rolling"] = rev_df["revenue"].rolling(7).mean()
            fig.add_trace(go.Scatter(
                x=rev_df["date"], y=rev_df["rolling"],
                name="7-Day Avg", line=dict(color="#f9a825", width=2, dash="dot")
            ))
            fig.update_layout(
                height=300, margin=dict(l=0,r=0,t=10,b=0),
                legend=dict(orientation="h", y=1.1),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f0f0f0")
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Revenue by Month")
        if not rev_df.empty:
            rev_df["month"] = rev_df["date"].dt.to_period("M").astype(str)
            monthly = rev_df.groupby("month")["revenue"].sum().tail(6).reset_index()
            fig2 = go.Figure(go.Bar(
                x=monthly["month"], y=monthly["revenue"],
                marker_color="#1a237e",
                text=[f"₨{v/1e6:.1f}M" for v in monthly["revenue"]],
                textposition="outside"
            ))
            fig2.update_layout(
                height=300, margin=dict(l=0,r=0,t=10,b=30),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False), yaxis=dict(showticklabels=False)
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Branch performance
    st.markdown("---")
    st.subheader("Branch Performance")
    branch_df = get_branch_df()
    col_a, col_b = st.columns([1, 1])

    with col_a:
        if not branch_df.empty:
            branch_sorted = branch_df.sort_values("total_revenue", ascending=True).tail(6)
            fig3 = go.Figure(go.Bar(
                y=branch_sorted["branch_code"],
                x=branch_sorted["total_revenue"],
                orientation="h",
                marker_color="#1a237e",
                text=[f"₨{v/1e6:.1f}M" for v in branch_sorted["total_revenue"]],
                textposition="outside"
            ))
            fig3.update_layout(
                height=280, margin=dict(l=0,r=60,t=10,b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, showticklabels=False)
            )
            st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        if not branch_df.empty:
            display = branch_df.copy()
            display["total_revenue"]  = display["total_revenue"].apply(lambda x: f"₨{x/1e6:.2f}M")
            display["avg_balance"]    = display["avg_balance"].apply(lambda x: f"₨{x:,.0f}")
            display["fraud_rate_pct"] = display["fraud_rate_pct"].apply(lambda x: f"{x}%")
            if "churn_rate_pct" in display.columns:
                display["churn_rate_pct"] = display["churn_rate_pct"].apply(lambda x: f"{x}%")
            st.dataframe(display, use_container_width=True, hide_index=True)

    render_footer()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# BUSINESS ANALYST — Risk Monitor (Fraud + Churn)
# ══════════════════════════════════════════════════════════════════════════════
else:
    render_page_header("Risk Monitor", "Fraud detection & customer churn analytics", "🔍")

    if not loaded:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px;">
            <div style="font-size:4rem; margin-bottom:16px;">📤</div>
            <h2 style="color:#1a237e;">No Data Uploaded Yet</h2>
            <p style="color:#9e9e9e;">Upload your banking dataset to see risk insights here.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Data Upload →", type="primary"):
            st.switch_page("pages/Data_Upload.py")
        render_footer()
        st.stop()

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Transactions",  f"{summary.get('total_rows',0):,}", "💳")
    with c2: metric_card("Unique Customers",    f"{summary.get('total_customers',0):,}", "👥")
    with c3: metric_card("Fraud Transactions",
                         f"{summary.get('fraud_count',0):,}", "🚨",
                         delta=f"{summary.get('fraud_rate',0):.1f}% rate",
                         delta_color="negative" if summary.get('fraud_rate',0) > 2 else "normal")
    with c4: metric_card("Churned Customers",
                         f"{summary.get('churned_count',0):,}", "📉",
                         delta=f"{summary.get('churn_rate',0):.1f}% rate",
                         delta_color="negative" if summary.get('churn_rate',0) > 10 else "normal")

    st.markdown("<br/>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("Fraud vs Legitimate Transactions")
        if "is_fraud" in df.columns:
            fraud_n = int(df["is_fraud"].sum())
            legit_n = len(df) - fraud_n
            fig = go.Figure(go.Pie(
                labels=["Legitimate", "Fraudulent"],
                values=[legit_n, fraud_n],
                marker=dict(colors=["#1a237e", "#c62828"]),
                hole=0.5, textinfo="percent+label", textfont=dict(size=12)
            ))
            fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
                              showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Fraud by Merchant Category")
        if "is_fraud" in df.columns and "merchant_category" in df.columns:
            fraud_merch = df[df["is_fraud"] == 1].groupby("merchant_category").size().reset_index(name="count")
            fig2 = go.Figure(go.Bar(
                x=fraud_merch["merchant_category"],
                y=fraud_merch["count"],
                marker_color="#c62828",
                text=fraud_merch["count"], textposition="outside"
            ))
            fig2.update_layout(
                height=300, margin=dict(l=0,r=0,t=10,b=30),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#f0f0f0")
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.subheader("Churn Rate by City")
        if "is_churned" in df.columns and "city" in df.columns and "customer_id" in df.columns:
            city_churn = (df.drop_duplicates("customer_id")
                            .groupby("city")["is_churned"]
                            .mean() * 100).round(1).sort_values(ascending=False).reset_index()
            city_churn.columns = ["City", "Churn Rate %"]
            colors_churn = ["#c62828" if v > 25 else "#f57f17" if v > 15 else "#2e7d32"
                            for v in city_churn["Churn Rate %"]]
            fig3 = go.Figure(go.Bar(
                x=city_churn["City"], y=city_churn["Churn Rate %"],
                marker_color=colors_churn,
                text=[f"{v}%" for v in city_churn["Churn Rate %"]],
                textposition="outside"
            ))
            fig3.update_layout(
                height=280, margin=dict(l=0,r=0,t=10,b=40),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#f0f0f0")
            )
            st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        st.subheader("Fraud Transactions Over Time")
        if "is_fraud" in df.columns and "transaction_date" in df.columns:
            daily = df.copy()
            daily["transaction_date"] = pd.to_datetime(daily["transaction_date"])
            daily_fraud = daily.groupby("transaction_date")["is_fraud"].sum().reset_index()
            fig4 = go.Figure(go.Scatter(
                x=daily_fraud["transaction_date"], y=daily_fraud["is_fraud"],
                fill="tozeroy", line=dict(color="#c62828", width=2),
                fillcolor="rgba(198,40,40,0.08)"
            ))
            fig4.update_layout(
                height=280, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f0f0f0")
            )
            st.plotly_chart(fig4, use_container_width=True)

    render_footer()
