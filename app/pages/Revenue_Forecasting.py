import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from app.utils.session import require_auth
from app.utils.data_store import get_revenue_df, is_data_loaded
from app.components.theme import load_css, apply_theme, render_page_header, render_footer
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="IntelliBank — Revenue Forecasting", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
load_css()
user = require_auth()
apply_theme(st.session_state.get("theme", "light"))
render_sidebar()

render_page_header("Revenue Forecasting", "Facebook Prophet model with Pakistan-specific seasonality", "📈")

tab1, tab2, tab3 = st.tabs(["Forecast Dashboard", "Train on Uploaded Data", "Seasonality Analysis"])

# ─── Tab 1: Forecast Dashboard ────────────────────────────────────────────────
with tab1:
    st.subheader("Revenue Forecast")

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        forecast_days = st.selectbox("Forecast Period", [30, 60, 90, 180, 365],
                                      format_func=lambda x: f"{x} days")
    with col_ctrl2:
        show_intervals = st.toggle("Show Confidence Intervals", value=True)
    with col_ctrl3:
        show_components = st.toggle("Show Trend Components", value=False)

    try:
        from ml.forecast.predict import forecast, forecast_summary
        summary = forecast_summary(periods=forecast_days)
        forecast_df = pd.DataFrame(forecast(periods=forecast_days))
        forecast_df["date"] = pd.to_datetime(forecast_df["date"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Forecast Revenue", f"PKR {summary['total_forecast_revenue']/1e6:.2f}M")
        m2.metric("Avg Daily Revenue", f"PKR {summary['avg_daily_revenue']:,.0f}")
        m3.metric("Peak Day Revenue", f"PKR {summary['peak_revenue']:,.0f}",
                  delta=f"on {summary['peak_day']}")
        m4.metric("Growth Rate", f"{summary['growth_rate_pct']:+.1f}%")

        st.markdown("---")

        fig = go.Figure()
        today = datetime.now()
        hist = forecast_df[forecast_df["date"] <= today]
        future = forecast_df[forecast_df["date"] > today]

        fig.add_trace(go.Scatter(
            x=hist["date"], y=hist["forecast"],
            name="Historical", line=dict(color="#1a237e", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=future["date"], y=future["forecast"],
            name="Forecast", line=dict(color="#f9a825", width=2, dash="dash"),
        ))

        if show_intervals and "lower_bound" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([future["date"], future["date"][::-1]]),
                y=pd.concat([future["upper_bound"], future["lower_bound"][::-1]]),
                fill="toself", fillcolor="rgba(249,168,37,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="95% Confidence Interval",
            ))

        fig.add_vline(x=today, line_dash="dash", line_color="grey",
                      annotation_text="Today", annotation_position="top")
        fig.update_layout(
            height=400, title="Revenue Forecast",
            xaxis_title="Date", yaxis_title="Revenue (PKR)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

        if show_components:
            comp_c1, comp_c2 = st.columns(2)
            with comp_c1:
                fig_trend = px.line(forecast_df, x="date", y="trend",
                                    title="Trend Component", color_discrete_sequence=["#1a237e"])
                fig_trend.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                                        plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_trend, use_container_width=True)
            with comp_c2:
                if "weekly_seasonality" in forecast_df.columns:
                    fig_weekly = px.line(forecast_df.head(30), x="date", y="weekly_seasonality",
                                        title="Weekly Seasonality", color_discrete_sequence=["#f9a825"])
                    fig_weekly.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                                             plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_weekly, use_container_width=True)

        with st.expander("Forecast Data Table"):
            future_table = future[["date", "forecast", "lower_bound", "upper_bound"]].copy()
            future_table.columns = ["Date", "Forecast (PKR)", "Lower Bound", "Upper Bound"]
            st.dataframe(future_table, use_container_width=True)
            st.download_button("Download Forecast CSV", future_table.to_csv(index=False),
                               file_name="revenue_forecast.csv")

    except FileNotFoundError:
        st.info("Forecast model not trained yet. Go to **Train on Uploaded Data** tab to train.")
    except Exception as e:
        st.error(f"Forecast error: {e}")

# ─── Tab 2: Train on Uploaded Data ───────────────────────────────────────────
with tab2:
    st.subheader("Train Revenue Forecast Model")

    if is_data_loaded():
        rev_df = get_revenue_df()
        if not rev_df.empty:
            st.success(f"Uploaded dataset available — **{len(rev_df):,} daily revenue data points** "
                       f"({str(rev_df['date'].min().date())} → {str(rev_df['date'].max().date())})")

            # Preview chart
            fig_prev = go.Figure(go.Scatter(
                x=rev_df["date"], y=rev_df["revenue"],
                fill="tozeroy",
                line=dict(color="#1a237e", width=2),
                fillcolor="rgba(26,35,126,0.08)"
            ))
            fig_prev.update_layout(
                height=250, title="Historical Revenue from Uploaded Data",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f0f0f0"),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig_prev, use_container_width=True)

            if st.button("Train Forecast Model on Uploaded Data", type="primary"):
                with st.spinner("Training Prophet model..."):
                    try:
                        from ml.forecast.train import train as forecast_train
                        _, metrics = forecast_train(rev_df, date_col="date", value_col="revenue")
                        st.success("Revenue forecast model trained successfully!")
                        if metrics:
                            c1, c2 = st.columns(2)
                            c1.metric("MAE", f"{metrics.get('mae', 0):,.0f}")
                            c2.metric("MAPE", f"{metrics.get('mape', 0):.2%}")
                        st.info("Go to **Forecast Dashboard** tab to view predictions.")
                    except Exception as e:
                        st.error(str(e))
        else:
            st.warning("Uploaded dataset has no transaction_date or amount columns needed for forecasting.")
    else:
        st.info("No dataset uploaded yet. Go to **Data Upload** to upload your CSV first.")

    st.markdown("---")
    st.markdown("*Or upload a custom revenue file:*")
    uploaded = st.file_uploader("Upload Revenue CSV/Excel", type=["csv", "xlsx"], key="revenue_upload")
    if uploaded:
        df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
        st.dataframe(df.head(), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            date_col = st.selectbox("Date Column", df.columns.tolist())
        with c2:
            value_col = st.selectbox("Revenue Column", df.columns.tolist(),
                                      index=1 if len(df.columns) > 1 else 0)

        if st.button("Train from This File", type="primary"):
            with st.spinner("Training Prophet model..."):
                try:
                    from ml.forecast.train import train as forecast_train
                    _, metrics = forecast_train(df, date_col=date_col, value_col=value_col)
                    st.success("Revenue forecast model trained successfully!")
                    if metrics:
                        st.metric("MAE", f"{metrics.get('mae', 0):,.2f}")
                        st.metric("MAPE", f"{metrics.get('mape', 0):.2%}")
                except Exception as e:
                    st.error(str(e))

# ─── Tab 3: Seasonality ───────────────────────────────────────────────────────
with tab3:
    st.subheader("Pakistan Banking Seasonality Analysis")
    st.markdown("Revenue patterns based on Pakistani banking calendar and holidays.")

    # If uploaded data available, show actual monthly revenue
    if is_data_loaded():
        rev_df = get_revenue_df()
        if not rev_df.empty:
            rev_df["month"] = rev_df["date"].dt.month
            monthly = rev_df.groupby("month")["revenue"].mean().reset_index()
            monthly["month_name"] = monthly["month"].map({
                1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
            })
            overall_avg = monthly["revenue"].mean()
            monthly["seasonal_index"] = (monthly["revenue"] / overall_avg).round(3)

            fig_actual = go.Figure(go.Bar(
                x=monthly["month_name"], y=monthly["seasonal_index"],
                marker_color=["#f9a825" if v > 1 else "#1a237e" for v in monthly["seasonal_index"]],
                text=[f"{v:.2f}x" for v in monthly["seasonal_index"]],
                textposition="outside"
            ))
            fig_actual.update_layout(height=350, title="Actual Monthly Seasonality (from your data)",
                                     paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig_actual.add_hline(y=1.0, line_dash="dash", line_color="grey", annotation_text="Baseline")
            st.plotly_chart(fig_actual, use_container_width=True)
            st.caption("Based on your uploaded dataset")
            st.markdown("---")

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    seasonal_index = [0.85, 0.88, 0.95, 0.92, 1.10, 0.90,
                      1.05, 1.25, 1.00, 0.98, 1.12, 1.30]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=seasonal_index,
                         marker_color=["#f9a825" if v > 1 else "#1a237e" for v in seasonal_index],
                         text=[f"{v:.2f}x" for v in seasonal_index], textposition="outside"))
    fig.update_layout(height=350, title="Pakistan Banking Seasonality Index (Industry Benchmark)",
                      xaxis_title="Month", yaxis_title="Seasonal Index (1.0 = average)",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.add_hline(y=1.0, line_dash="dash", line_color="grey", annotation_text="Baseline")
    st.plotly_chart(fig, use_container_width=True)

    holiday_df = pd.DataFrame({
        "Holiday": ["Eid ul-Fitr", "Eid ul-Adha", "Independence Day", "Pakistan Day",
                    "Labour Day", "Ashura", "New Year"],
        "Impact": ["+35%", "+28%", "+15%", "+5%", "-20%", "-15%", "+10%"],
        "Duration (days)": [3, 3, 1, 1, 1, 2, 1],
    })
    st.dataframe(holiday_df, use_container_width=True, hide_index=True)

render_footer()
