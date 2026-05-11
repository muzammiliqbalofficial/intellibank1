import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.express as px

from app.utils.session import require_permission, get_db_session
from app.components.theme import load_css, apply_theme, render_page_header, render_footer
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="IntelliBank — Audit Trail", page_icon="📋", layout="wide", initial_sidebar_state="expanded")
load_css()
user = require_permission("view_audit_logs")
apply_theme(st.session_state.get("theme", "light"))
render_sidebar()

render_page_header("Audit Trail", "Complete activity log for compliance and security monitoring", "📋")

# ── Filters ───────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    filter_action = st.text_input("Filter by Action", placeholder="e.g., LOGIN")
with col_f2:
    filter_resource = st.selectbox("Resource", ["All", "auth", "users", "fraud", "churn", "nlp"])
with col_f3:
    filter_success = st.selectbox("Status", ["All", "Success", "Failed"])
with col_f4:
    limit = st.selectbox("Show", [50, 100, 200, 500], index=0)

# ── Fetch Logs ─────────────────────────────────────────────────────────────────
db = get_db_session()
try:
    from services.auth_service import AuditService
    from db.models import AuditLog

    query = db.query(AuditLog)
    if filter_action:
        query = query.filter(AuditLog.action.ilike(f"%{filter_action}%"))
    if filter_resource != "All":
        query = query.filter(AuditLog.resource == filter_resource)
    if filter_success == "Success":
        query = query.filter(AuditLog.is_success == True)
    elif filter_success == "Failed":
        query = query.filter(AuditLog.is_success == False)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
finally:
    db.close()

if logs:
    # Summary metrics
    log_df = pd.DataFrame([{
        "ID": l.id,
        "User ID": l.user_id,
        "Action": l.action,
        "Resource": l.resource,
        "IP Address": l.ip_address or "N/A",
        "Status": "✅ Success" if l.is_success else "❌ Failed",
        "Timestamp": str(l.created_at)[:19] if l.created_at else "N/A",
    } for l in logs])

    total = len(log_df)
    failed = (log_df["Status"] == "❌ Failed").sum()
    unique_users = log_df["User ID"].nunique()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Events", f"{total:,}")
    m2.metric("Failed Events", f"{failed:,}", delta_color="inverse" if failed > 0 else "off")
    m3.metric("Unique Users", f"{unique_users}")

    # Action distribution chart
    action_counts = log_df["Action"].value_counts().head(10).reset_index()
    action_counts.columns = ["Action", "Count"]
    fig = px.bar(action_counts, x="Count", y="Action", orientation="h",
                 color_discrete_sequence=["#1a237e"], title="Top Actions")
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=40, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # Logs table
    st.dataframe(log_df, use_container_width=True, hide_index=True)

    st.download_button("Export Audit Logs (CSV)", log_df.to_csv(index=False),
                       file_name="audit_trail.csv", mime="text/csv")
else:
    st.info("No audit logs found for the selected filters.")

render_footer()
