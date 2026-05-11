import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.utils.session import require_auth
from app.utils.data_store import get_branch_df, is_data_loaded
from app.components.theme import load_css, apply_theme, render_page_header, render_footer
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="IntelliBank — Branch Analysis", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")
load_css()
user = require_auth()
apply_theme(st.session_state.get("theme", "light"))
render_sidebar()

render_page_header("Branch Comparison & Leaderboard", "Multi-branch performance benchmarking", "🏢")

# ── Load branch data from uploaded dataset or fall back to sample ─────────────
CITY_COORDS = {
    "Karachi":   (24.8607, 67.0011),
    "Lahore":    (31.5204, 74.3587),
    "Islamabad": (33.6844, 73.0479),
    "Peshawar":  (34.0151, 71.5249),
    "Quetta":    (30.1798, 66.9750),
    "Multan":    (30.1575, 71.5249),
}

BRANCH_CITY_MAP = {
    "KHI-001": "Karachi", "LHR-001": "Lahore", "ISB-001": "Islamabad",
    "PEW-001": "Peshawar", "QTA-001": "Quetta", "MUL-001": "Multan",
}

if is_data_loaded():
    raw = get_branch_df()
    if not raw.empty:
        branch_data = raw.rename(columns={
            "branch_code":    "Code",
            "total_revenue":  "Revenue_M",
            "transactions":   "Transactions",
            "customers":      "Customers",
            "fraud_rate_pct": "Fraud_Rate",
            "avg_balance":    "Avg_Balance_K",
        }).copy()
        branch_data["Revenue_M"]    = branch_data["Revenue_M"] / 1e6
        branch_data["Avg_Balance_K"] = branch_data["Avg_Balance_K"] / 1000
        branch_data["Churn_Rate"]   = branch_data.get("churn_rate_pct", pd.Series([0] * len(branch_data))).fillna(0)
        branch_data["Growth_Rate"]  = 0.0   # not derivable without historical data
        branch_data["City"]         = branch_data["Code"].map(BRANCH_CITY_MAP).fillna("Unknown")
        branch_data["Branch"]       = branch_data["Code"]
        using_real_data = True
    else:
        using_real_data = False
else:
    using_real_data = False

if not using_real_data:
    st.info("No dataset uploaded yet — showing sample data. Upload a CSV on the **Data Upload** page to see real branch analytics.")
    branch_data = pd.DataFrame({
        "Branch": ["Karachi Main", "Lahore Central", "Islamabad Capital", "Peshawar", "Quetta"],
        "Code":   ["KHI-001", "LHR-001", "ISB-001", "PEW-001", "QTA-001"],
        "City":   ["Karachi", "Lahore", "Islamabad", "Peshawar", "Quetta"],
        "Revenue_M":    [45.2, 38.7, 31.4, 18.9, 12.3],
        "Transactions": [12450, 9870, 8230, 5120, 3200],
        "Customers":    [3200, 2750, 2100, 1400, 890],
        "Fraud_Rate":   [1.2, 0.9, 1.8, 2.1, 0.7],
        "Churn_Rate":   [8.5, 12.3, 9.1, 15.2, 6.8],
        "Avg_Balance_K":[125.4, 118.7, 142.3, 89.5, 76.2],
        "Growth_Rate":  [12.5, 8.3, 15.7, -2.1, 5.4],
    })


def compute_kpi_score(row):
    revenue_score = min(row["Revenue_M"] / max(branch_data["Revenue_M"].max(), 1) * 40, 40)
    fraud_score   = max(0, (3 - row["Fraud_Rate"]) / 3 * 20)
    churn_score   = max(0, (20 - row["Churn_Rate"]) / 20 * 20)
    growth_score  = min(max(row.get("Growth_Rate", 0), -10) + 10, 20) / 20 * 20
    return round(revenue_score + fraud_score + churn_score + growth_score, 1)


branch_data["KPI Score"] = branch_data.apply(compute_kpi_score, axis=1)
branch_data["Rank"]      = branch_data["KPI Score"].rank(ascending=False).astype(int)
branch_data = branch_data.sort_values("Rank").reset_index(drop=True)

tab1, tab2, tab3, tab4 = st.tabs(["Leaderboard", "KPI Comparison", "Head-to-Head", "Performance Map"])

# ─── Tab 1: Leaderboard ───────────────────────────────────────────────────────
with tab1:
    st.subheader("Branch Leaderboard")
    if using_real_data:
        st.caption("Data from your uploaded dataset")

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for _, row in branch_data.iterrows():
        medal = medals.get(row["Rank"], f"#{int(row['Rank'])}")
        col_rank, col_name, col_rev, col_txn, col_fraud, col_churn, col_score = st.columns(
            [0.5, 1.5, 1, 1, 0.8, 0.8, 1]
        )
        col_rank.markdown(f"### {medal}")
        col_name.markdown(f"**{row['Branch']}**<br/><small>{row['City']}</small>",
                          unsafe_allow_html=True)
        col_rev.metric("Revenue", f"₨{row['Revenue_M']:.1f}M")
        col_txn.metric("Transactions", f"{int(row['Transactions']):,}")
        col_fraud.metric("Fraud Rate", f"{row['Fraud_Rate']:.1f}%")
        col_churn.metric("Churn Rate", f"{row['Churn_Rate']:.1f}%")
        col_score.metric("KPI Score", f"{row['KPI Score']}/100")
        st.divider()

# ─── Tab 2: KPI Comparison ────────────────────────────────────────────────────
with tab2:
    st.subheader("Multi-KPI Branch Comparison")

    available_metrics = [c for c in ["Revenue_M", "Transactions", "Customers",
                                      "Avg_Balance_K", "Fraud_Rate", "Churn_Rate"]
                         if c in branch_data.columns]
    selected_metric = st.selectbox("Select KPI", available_metrics,
                                    format_func=lambda x: x.replace("_", " "))

    fig = px.bar(branch_data.sort_values(selected_metric, ascending=False),
                 x="Branch", y=selected_metric,
                 color="KPI Score",
                 color_continuous_scale=["#c62828", "#f9a825", "#2e7d32"],
                 title=f"Branch Comparison: {selected_metric.replace('_', ' ')}",
                 text=selected_metric)
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Multi-Dimensional Performance Radar")
    radar_categories = ["Revenue", "Customer Volume", "Low Fraud", "Low Churn"]
    selected_branches = st.multiselect("Select Branches", branch_data["Branch"].tolist(),
                                        default=branch_data["Branch"].tolist()[:3])

    fig_radar = go.Figure()
    colors_radar = ["#1a237e", "#f9a825", "#2e7d32", "#c62828", "#7b1fa2", "#00838f"]
    max_rev = branch_data["Revenue_M"].max() or 1
    max_cust = branch_data["Customers"].max() or 1

    for i, br_name in enumerate(selected_branches):
        row = branch_data[branch_data["Branch"] == br_name].iloc[0]
        vals = [
            row["Revenue_M"] / max_rev * 100,
            row["Customers"] / max_cust * 100,
            max(0, (3 - row["Fraud_Rate"]) / 3 * 100),
            max(0, (20 - row["Churn_Rate"]) / 20 * 100),
        ]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=radar_categories + [radar_categories[0]],
            fill="toself",
            name=br_name,
            line_color=colors_radar[i % len(colors_radar)],
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=400, paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ─── Tab 3: Head-to-Head ─────────────────────────────────────────────────────
with tab3:
    st.subheader("Head-to-Head Branch Comparison")
    c1, c2 = st.columns(2)
    with c1:
        branch_a = st.selectbox("Branch A", branch_data["Branch"].tolist(), index=0)
    with c2:
        branch_b = st.selectbox("Branch B", branch_data["Branch"].tolist(),
                                 index=min(1, len(branch_data) - 1))

    if branch_a != branch_b:
        a = branch_data[branch_data["Branch"] == branch_a].iloc[0]
        b = branch_data[branch_data["Branch"] == branch_b].iloc[0]

        metrics_compare = [m for m in ["Revenue_M", "Transactions", "Customers",
                                        "Fraud_Rate", "Churn_Rate", "Avg_Balance_K", "KPI Score"]
                           if m in branch_data.columns]
        lower_is_better = {"Fraud_Rate", "Churn_Rate"}
        compare_rows = []
        for m in metrics_compare:
            val_a, val_b = float(a[m]), float(b[m])
            if m in lower_is_better:
                winner = "A" if val_a < val_b else "B"
            else:
                winner = "A" if val_a > val_b else "B"
            compare_rows.append({
                "KPI": m.replace("_", " "),
                branch_a: round(val_a, 2),
                branch_b: round(val_b, 2),
                "Winner": "🏆 " + (branch_a if winner == "A" else branch_b),
            })

        st.dataframe(pd.DataFrame(compare_rows), use_container_width=True, hide_index=True)
        wins_a = sum(1 for r in compare_rows if r["Winner"].endswith(branch_a))
        if wins_a > len(compare_rows) // 2:
            st.success(f"**{branch_a}** wins {wins_a}/{len(compare_rows)} metrics!")
        else:
            st.success(f"**{branch_b}** wins {len(compare_rows)-wins_a}/{len(compare_rows)} metrics!")

# ─── Tab 4: Performance Map ───────────────────────────────────────────────────
with tab4:
    st.subheader("Branch Performance Map")

    branch_map = branch_data.copy()
    branch_map["lat"] = branch_map["City"].map(lambda c: CITY_COORDS.get(c, (30, 70))[0])
    branch_map["lon"] = branch_map["City"].map(lambda c: CITY_COORDS.get(c, (30, 70))[1])

    fig_map = px.scatter_mapbox(
        branch_map, lat="lat", lon="lon",
        size="Revenue_M", color="KPI Score",
        color_continuous_scale="RdYlGn",
        hover_name="Branch",
        hover_data={"Revenue_M": True, "KPI Score": True, "lat": False, "lon": False},
        size_max=40, zoom=5,
        center={"lat": 30.3753, "lon": 69.3451},
        mapbox_style="open-street-map",
        title="Branch Locations & Performance",
    )
    fig_map.update_layout(height=450, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

render_footer()
