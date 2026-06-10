import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.utils.session import require_auth
from app.utils.data_store import get_dataset, is_data_loaded, get_summary, get_branch_df, get_revenue_df, load_snapshot, get_data_lineage
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
load_snapshot()          # load from DB if session_state is empty
df      = get_dataset()
loaded  = is_data_loaded()
summary = get_summary()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD — User management & system logs
# ══════════════════════════════════════════════════════════════════════════════
if role == "admin":
    render_page_header("Admin Dashboard", "User management and system activity overview", "🔐")

    from app.utils.session import get_db_session
    from db.models import User, AuditLog, UserRole
    from services.auth_service import AuthService

    def _load_users_logs():
        db = get_db_session()
        try:
            u = db.query(User).all()
            l = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all()
            return u, l
        except Exception:
            return [], []
        finally:
            db.close()

    users, logs = _load_users_logs()

    # KPIs
    c1, c2, c3 = st.columns(3)
    role_counts = {}
    for u in users:
        rk = u.role.value if hasattr(u.role, "value") else str(u.role)
        role_counts[rk] = role_counts.get(rk, 0) + 1

    with c1: metric_card("Total Users",       str(len(users)),                                "👥")
    with c2: metric_card("Bank Managers",     str(role_counts.get("bank_manager", 0)),        "🟡")
    with c3: metric_card("Business Analysts", str(role_counts.get("business_analyst", 0)),    "🟢")

    st.markdown("<br/>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👥 All Users", "➕ Add User", "📋 Activity Logs"])

    # ── Tab 1: All Users ──────────────────────────────────────────────────────
    with tab1:
        col_l, col_r = st.columns([3, 2])
        with col_l:
            st.subheader("Registered Users")
            if users:
                for u in users:
                    u_role = u.role.value if hasattr(u.role, "value") else str(u.role)
                    c_info, c_badge, c_del = st.columns([3, 2, 1])
                    with c_info:
                        st.markdown(f"**{u.username}**  \n{u.email}")
                    with c_badge:
                        badge_color = {"admin":"#c62828","bank_manager":"#f57f17","business_analyst":"#2e7d32"}.get(u_role,"#1a237e")
                        st.markdown(
                            f"<span style='background:{badge_color}20;color:{badge_color};"
                            f"padding:3px 10px;border-radius:12px;font-size:0.78rem;"
                            f"font-weight:600;border:1px solid {badge_color}60'>{u_role}</span>",
                            unsafe_allow_html=True
                        )
                    with c_del:
                        if u.username != user.get("username"):
                            if st.button("🗑️", key=f"del_{u.id}", help=f"Delete {u.username}"):
                                db2 = get_db_session()
                                try:
                                    target = db2.query(User).filter(User.id == u.id).first()
                                    if target:
                                        db2.delete(target)
                                        db2.commit()
                                    st.success(f"User '{u.username}' deleted.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                                finally:
                                    db2.close()
                        else:
                            st.caption("(you)")
                    st.divider()
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
                                  paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                                  clickmode='none')
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Tab 2: Add User ───────────────────────────────────────────────────────
    with tab2:
        st.subheader("Create New User")
        with st.form("add_user_form", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            with fc1:
                new_username = st.text_input("Username *")
                new_email    = st.text_input("Email *")
            with fc2:
                new_password = st.text_input("Password *", type="password")
                new_role     = st.selectbox("Role *", ["bank_manager", "business_analyst"],
                                            format_func=lambda x: "🟡 Bank Manager" if x == "bank_manager" else "🟢 Business Analyst")
            submitted = st.form_submit_button("✅ Create User", type="primary", use_container_width=True)

        if submitted:
            if not all([new_username.strip(), new_email.strip(), new_password.strip()]):
                st.error("All fields are required.")
            else:
                role_map = {
                    "bank_manager":     UserRole.BANK_MANAGER,
                    "business_analyst": UserRole.BUSINESS_ANALYST,
                }
                db3 = get_db_session()
                try:
                    AuthService.create_user(db3, new_username.strip(), new_email.strip(),
                                            new_password, new_username.strip(), role_map[new_role])
                    st.success(f"✅ User **{new_username}** created successfully as **{new_role}**!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create user: {e}")
                finally:
                    db3.close()

    # ── Tab 3: Activity Logs ──────────────────────────────────────────────────
    with tab3:
        st.subheader("Recent Activity Logs")
        if logs:
            log_data = [{
                "Action":    l.action,
                "User ID":   str(l.user_id or "—"),
                "Resource":  l.resource or "—",
                "Status":    "✅" if l.is_success else "❌",
                "Timestamp": str(l.created_at)[:16] if l.created_at else "",
            } for l in logs]
            st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
        else:
            st.info("No activity logs yet.")

    render_footer()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# BANK MANAGER — Executive Command Center
# ══════════════════════════════════════════════════════════════════════════════
elif role == "bank_manager":
    render_page_header("Executive Command Center",
                       "Strategic overview — AI-driven insights from analyst reports", "📊")

    # ── KPI Row (always visible) ───────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Revenue",
                         f"₨{summary.get('total_revenue',0)/1e6:.1f}M" if loaded else "No Data", "💰")
    with c2: metric_card("Total Customers",
                         f"{summary.get('total_customers',0):,}" if loaded else "No Data", "👥")
    with c3: metric_card("Fraud Alert Rate",
                         f"{summary.get('fraud_rate',0):.1f}%" if loaded else "No Data", "🚨",
                         delta="High Risk" if loaded and summary.get('fraud_rate',0) > 2 else "Normal",
                         delta_color="negative" if loaded and summary.get('fraud_rate',0) > 2 else "normal")
    with c4: metric_card("Churn Rate",
                         f"{summary.get('churn_rate',0):.1f}%" if loaded else "No Data", "📉",
                         delta="High Risk" if loaded and summary.get('churn_rate',0) > 10 else "Normal",
                         delta_color="negative" if loaded and summary.get('churn_rate',0) > 10 else "normal")

    st.markdown("<br/>", unsafe_allow_html=True)

    if not loaded:
        st.info("📤 No dataset uploaded yet. Ask your analyst to upload data to see full insights.")
    else:
        # ── Data Lineage Bar ───────────────────────────────────────────────────
        lin = get_data_lineage()
        st.caption(
            f"**Data Source:** {lin['filename']}  ·  "
            f"**Rows:** {lin['rows']:,}  ·  "
            f"**Period:** {lin['date_from']} to {lin['date_to']}  ·  "
            f"**Loaded:** {lin['loaded_at']}  ·  Source: uploaded CSV → session cache"
        )

        # ── Revenue Trend ──────────────────────────────────────────────────────
        rev_df = get_revenue_df()
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.subheader("Revenue Trend")
            if not rev_df.empty:
                rev_df["rolling"] = rev_df["revenue"].rolling(7).mean()
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=rev_df["date"], y=rev_df["revenue"],
                    name="Daily Revenue", fill="tozeroy",
                    line=dict(color="#1a237e", width=2),
                    fillcolor="rgba(26,35,126,0.08)"
                ))
                fig.add_trace(go.Scatter(
                    x=rev_df["date"], y=rev_df["rolling"],
                    name="7-Day Avg", line=dict(color="#f9a825", width=2, dash="dot")
                ))
                fig.update_layout(
                    height=280, margin=dict(l=0,r=0,t=10,b=0),
                    legend=dict(orientation="h", y=1.1),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f0f0f0")
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.subheader("Monthly Revenue")
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
                    height=280, margin=dict(l=0,r=0,t=10,b=30),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False), yaxis=dict(showticklabels=False)
                )
                st.plotly_chart(fig2, use_container_width=True)

        # ── Risk Summary (from Analyst work) ──────────────────────────────────
        st.markdown("---")
        st.subheader("Risk Overview — Analyst Findings")
        r1, r2 = st.columns(2)

        with r1:
            st.markdown("##### 🚨 Fraud Summary")
            if "is_fraud" in df.columns:
                fraud_n = int(df["is_fraud"].sum())
                legit_n = len(df) - fraud_n
                fig_f = go.Figure(go.Pie(
                    labels=["Legitimate", "Fraudulent"],
                    values=[legit_n, fraud_n],
                    marker=dict(colors=["#1a237e", "#c62828"]),
                    hole=0.5, textinfo="percent+label"
                ))
                fig_f.update_layout(height=250, margin=dict(l=0,r=0,t=10,b=0),
                                    showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                                    clickmode='none')
                st.plotly_chart(fig_f, use_container_width=True, config={"displayModeBar": False})
                st.markdown(f"**{fraud_n:,}** fraudulent out of **{len(df):,}** total transactions")

        with r2:
            st.markdown("##### 📉 Churn Summary")
            if "is_churned" in df.columns and "city" in df.columns and "customer_id" in df.columns:
                city_churn = (df.drop_duplicates("customer_id")
                                .groupby("city")["is_churned"]
                                .mean() * 100).round(1).sort_values(ascending=False).head(5).reset_index()
                city_churn.columns = ["City", "Churn %"]
                colors_c = ["#c62828" if v > 25 else "#f57f17" if v > 15 else "#2e7d32"
                            for v in city_churn["Churn %"]]
                fig_c = go.Figure(go.Bar(
                    x=city_churn["City"], y=city_churn["Churn %"],
                    marker_color=colors_c,
                    text=[f"{v}%" for v in city_churn["Churn %"]],
                    textposition="outside"
                ))
                fig_c.update_layout(
                    height=250, margin=dict(l=0,r=0,t=10,b=30),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(gridcolor="#f0f0f0")
                )
                st.plotly_chart(fig_c, use_container_width=True)

        # ── Branch Performance ─────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("Branch Performance")
        branch_df = get_branch_df()
        if not branch_df.empty:
            display = branch_df.copy()
            display["total_revenue"]  = display["total_revenue"].apply(lambda x: f"₨{x/1e6:.2f}M")
            display["avg_balance"]    = display["avg_balance"].apply(lambda x: f"₨{x:,.0f}")
            display["fraud_rate_pct"] = display["fraud_rate_pct"].apply(lambda x: f"{x}%")
            if "churn_rate_pct" in display.columns:
                display["churn_rate_pct"] = display["churn_rate_pct"].apply(lambda x: f"{x}%")
            st.dataframe(display, use_container_width=True, hide_index=True)

        # ── Generate Report ────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("Generate Executive Report")
        st.caption("Download a business-oriented summary report for strategic decision-making.")
        rpt_col1, rpt_col2, rpt_col3 = st.columns([1, 1, 2])
        with rpt_col1:
            rpt_fmt = st.selectbox("Format", ["PDF", "Excel"], key="mgr_rpt_fmt")
        with rpt_col2:
            st.markdown("<br/>", unsafe_allow_html=True)
            gen_rpt = st.button("Generate Report", type="primary", use_container_width=True, key="mgr_gen_rpt")

        if gen_rpt:
            from services.report_service import generate_manager_pdf_report, generate_manager_excel_report
            rev_df_rpt    = get_revenue_df()
            branch_df_rpt = get_branch_df()
            with st.spinner("Generating executive report..."):
                if rpt_fmt == "PDF":
                    rpt_bytes = generate_manager_pdf_report(summary, rev_df_rpt, branch_df_rpt)
                    st.download_button(
                        label="Download Executive Report (PDF)",
                        data=rpt_bytes,
                        file_name=f"IntelliBank_Executive_Report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True,
                    )
                else:
                    rpt_bytes = generate_manager_excel_report(summary, rev_df_rpt, branch_df_rpt)
                    st.download_button(
                        label="Download Executive Report (Excel)",
                        data=rpt_bytes,
                        file_name=f"IntelliBank_Executive_Report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                    )

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

    # ── Data Lineage Bar ──────────────────────────────────────────────────────
    lin = get_data_lineage()
    st.caption(
        f"**Data Source:** {lin['filename']}  ·  "
        f"**Rows:** {lin['rows']:,}  ·  "
        f"**Period:** {lin['date_from']} to {lin['date_to']}  ·  "
        f"**Loaded:** {lin['loaded_at']}  ·  Source: uploaded CSV → session cache"
    )

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
        else:
            fraud_n = summary.get("fraud_count", 0)
            legit_n = summary.get("total_rows", 0) - fraud_n
        if fraud_n > 0 or legit_n > 0:
            fig = go.Figure(go.Pie(
                labels=["Legitimate", "Fraudulent"],
                values=[legit_n, fraud_n],
                marker=dict(colors=["#1a237e", "#c62828"]),
                hole=0.5, textinfo="percent+label", textfont=dict(size=12)
            ))
            fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
                              showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              clickmode='none')
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_r:
        st.subheader("Fraud by Merchant Category")
        if "is_fraud" in df.columns and "merchant_category" in df.columns:
            fraud_merch = df[df["is_fraud"] == 1].groupby("merchant_category").size().reset_index(name="count")
        else:
            snap_fm = st.session_state.get("_snap_fraud_merchant", [])
            fraud_merch = pd.DataFrame(snap_fm) if snap_fm else pd.DataFrame()
        if not fraud_merch.empty:
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
        else:
            snap_cc = st.session_state.get("_snap_churn_city", [])
            if snap_cc:
                city_churn = pd.DataFrame(snap_cc).rename(columns={"city": "City", "churn_rate": "Churn Rate %"})
                city_churn = city_churn.sort_values("Churn Rate %", ascending=False)
            else:
                city_churn = pd.DataFrame()
        if not city_churn.empty:
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
            daily_fraud.columns = ["date", "count"]
        else:
            snap_df = st.session_state.get("_snap_daily_fraud", [])
            daily_fraud = pd.DataFrame(snap_df) if snap_df else pd.DataFrame()
            if not daily_fraud.empty:
                daily_fraud["date"] = pd.to_datetime(daily_fraud["date"])
        if not daily_fraud.empty:
            fig4 = go.Figure(go.Scatter(
                x=daily_fraud["date"], y=daily_fraud["count"],
                fill="tozeroy", line=dict(color="#c62828", width=2),
                fillcolor="rgba(198,40,40,0.08)"
            ))
            fig4.update_layout(
                height=280, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f0f0f0")
            )
            st.plotly_chart(fig4, use_container_width=True)

    # ── Generate Technical Report ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Generate Technical Report")
    st.caption("Export a detailed technical analysis report including fraud, churn, and branch statistics.")
    rc1, rc2, rc3 = st.columns([1, 1, 2])
    with rc1:
        ana_rpt_fmt = st.selectbox("Format", ["PDF", "Excel", "CSV"], key="ana_rpt_fmt")
    with rc2:
        st.markdown("<br/>", unsafe_allow_html=True)
        gen_ana_rpt = st.button("Generate Report", type="primary", use_container_width=True, key="ana_gen_rpt")

    if gen_ana_rpt:
        from services.report_service import generate_analyst_pdf_report, generate_analyst_excel_report, dataframe_to_csv
        fname_ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
        with st.spinner("Generating technical report..."):
            if ana_rpt_fmt == "PDF":
                rpt_bytes = generate_analyst_pdf_report(df, summary)
                st.download_button(
                    label="Download Technical Report (PDF)",
                    data=rpt_bytes,
                    file_name=f"IntelliBank_Technical_Report_{fname_ts}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            elif ana_rpt_fmt == "Excel":
                rpt_bytes = generate_analyst_excel_report(df, summary)
                st.download_button(
                    label="Download Technical Report (Excel)",
                    data=rpt_bytes,
                    file_name=f"IntelliBank_Technical_Report_{fname_ts}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )
            else:
                csv_str = dataframe_to_csv(df)
                st.download_button(
                    label="Download Dataset (CSV)",
                    data=csv_str,
                    file_name=f"IntelliBank_Dataset_{fname_ts}.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True,
                )

    render_footer()
