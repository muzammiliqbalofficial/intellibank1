import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

from app.utils.session import require_auth
from app.utils.data_store import save_dataset, get_dataset, is_data_loaded, get_summary
from app.components.theme import load_css, apply_theme, render_page_header, render_footer
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="IntelliBank — Data Upload", page_icon="📤", layout="wide", initial_sidebar_state="expanded")
load_css()
user = require_auth()
apply_theme(st.session_state.get("theme", "light"))
render_sidebar()

render_page_header(
    "Data Upload & Training",
    "Upload your unified banking dataset — all models train automatically",
    "📤"
)

# ── Already loaded indicator ──────────────────────────────────────────────────
if is_data_loaded():
    summary = get_summary()
    st.success(f"Dataset loaded: **{summary.get('total_rows',0):,} transactions** | "
               f"**{summary.get('total_customers',0):,} customers** | "
               f"Date: {summary.get('date_from','')} → {summary.get('date_to','')}")

# ── Upload Section ─────────────────────────────────────────────────────────────
st.markdown("### Upload Dataset")
st.markdown("""
<div class="info-card">
<b>Expected columns in your CSV:</b><br/>
<code>customer_id, age, gender, city, branch_code, credit_score, tenure_years,
account_balance, estimated_salary, num_products, has_credit_card, is_active_member,
is_churned, transaction_id, transaction_date, amount, merchant_category,
transaction_type, hour, day_of_week, is_weekend, is_fraud</code>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Drop your CSV file here",
    type=["csv", "xlsx"],
    help="Single unified dataset with customer + transaction data"
)

if uploaded:
    with st.spinner("Reading file..."):
        df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)

    st.success(f"File loaded: **{uploaded.name}** — {len(df):,} rows × {len(df.columns)} columns")

    # ── Preview ────────────────────────────────────────────────────────────────
    with st.expander("Preview Data (first 10 rows)", expanded=True):
        st.dataframe(df.head(10), use_container_width=True)

    # ── Data Quality ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Data Quality Report")

    q1, q2, q3, q4, q5 = st.columns(5)
    q1.metric("Total Rows",       f"{len(df):,}")
    q2.metric("Columns",          f"{len(df.columns)}")
    q3.metric("Missing Values",   f"{df.isnull().sum().sum():,}")
    q4.metric("Duplicate Rows",   f"{df.duplicated().sum():,}")
    q5.metric("Memory",           f"{df.memory_usage(deep=True).sum()/1024:.0f} KB")

    col1, col2 = st.columns(2)
    with col1:
        null_pct = (df.isnull().sum() / len(df) * 100).round(2)
        missing  = null_pct[null_pct > 0].sort_values(ascending=False)
        if not missing.empty:
            fig = px.bar(x=missing.index, y=missing.values,
                         labels={"x":"Column","y":"Missing %"},
                         color=missing.values, color_continuous_scale="Reds",
                         title="Missing Values %")
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=40,b=0),
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No missing values — clean dataset!")

    with col2:
        if "is_fraud" in df.columns:
            fraud_counts = df["is_fraud"].value_counts()
            fig2 = go.Figure(go.Pie(
                labels=["Legitimate","Fraudulent"],
                values=[fraud_counts.get(0,0), fraud_counts.get(1,0)],
                marker_colors=["#1a237e","#c62828"],
                hole=0.45
            ))
            fig2.update_layout(height=280, title="Fraud Distribution",
                                margin=dict(l=0,r=0,t=40,b=0),
                                paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

    # ── Churn distribution ─────────────────────────────────────────────────────
    if "is_churned" in df.columns and "customer_id" in df.columns:
        cust_df = df.drop_duplicates("customer_id")
        churned = int(cust_df["is_churned"].sum())
        st.info(f"Unique customers: **{len(cust_df):,}** | "
                f"Churned: **{churned:,}** ({churned/len(cust_df):.1%}) | "
                f"Retained: **{len(cust_df)-churned:,}**")

    # ── Preprocess & Train ALL models ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("Preprocessing & Model Training")

    with st.form("train_form"):
        c1, c2 = st.columns(2)
        with c1:
            handle_missing = st.selectbox("Handle Missing Values",
                                          ["Mean/Mode Imputation","Drop Rows","Keep As-Is"])
            remove_dups    = st.checkbox("Remove Duplicate Rows", value=True)
        with c2:
            st.markdown("**Models to Train:**")
            train_fraud    = st.checkbox("Fraud Detection (XGBoost)", value="is_fraud"    in df.columns)
            train_churn    = st.checkbox("Churn Prediction (RF+LR)",  value="is_churned"  in df.columns)
            train_forecast = st.checkbox("Revenue Forecasting (Prophet)",
                                         value=("transaction_date" in df.columns and "amount" in df.columns))

        train_btn = st.form_submit_button("Preprocess & Train All Models",
                                          type="primary", use_container_width=True)

    if train_btn:
        progress = st.progress(0, text="Starting...")

        # ── Clean data ────────────────────────────────────────────────────────
        df_clean = df.copy()
        if remove_dups:
            df_clean = df_clean.drop_duplicates()

        if handle_missing == "Drop Rows":
            df_clean = df_clean.dropna()
        elif handle_missing == "Mean/Mode Imputation":
            for col in df_clean.select_dtypes(include=[np.number]).columns:
                df_clean[col].fillna(df_clean[col].mean(), inplace=True)
            for col in df_clean.select_dtypes(include=["object"]).columns:
                mode = df_clean[col].mode()
                df_clean[col].fillna(mode[0] if not mode.empty else "Unknown", inplace=True)

        save_dataset(df_clean)
        progress.progress(15, text="Data cleaned and saved...")

        results = {}

        # ── Train Fraud model ─────────────────────────────────────────────────
        if train_fraud and "is_fraud" in df_clean.columns:
            progress.progress(20, text="Training Fraud Detection model (XGBoost)...")
            try:
                from ml.fraud.train import train as fraud_train
                fraud_df = df_clean[["amount","merchant_category","transaction_type",
                                     "hour","day_of_week","is_weekend","is_fraud"]].copy()
                _, _, metrics = fraud_train(fraud_df)
                results["fraud"] = metrics
                progress.progress(45, text=f"Fraud model trained — AUC: {metrics['roc_auc']:.4f}")
            except Exception as e:
                st.warning(f"Fraud model: {e}")

        # ── Train Churn model ─────────────────────────────────────────────────
        if train_churn and "is_churned" in df_clean.columns:
            progress.progress(50, text="Training Churn Prediction model (RF+LR)...")
            try:
                from ml.churn.train import train as churn_train
                churn_df = df_clean.drop_duplicates("customer_id") if "customer_id" in df_clean.columns else df_clean
                churn_cols = ["credit_score","age","tenure_years","account_balance",
                              "num_products","has_credit_card","is_active_member",
                              "estimated_salary","city","gender","is_churned"]
                # rename to match model expectations
                rename_map = {"tenure_years":"tenure","account_balance":"balance",
                              "city":"geography","estimated_salary":"estimated_salary"}
                churn_df = churn_df[[c for c in churn_cols if c in churn_df.columns]].rename(columns=rename_map)
                _, _, metrics = churn_train(churn_df, target_col="is_churned")
                results["churn"] = metrics
                progress.progress(75, text=f"Churn model trained — AUC: {metrics['roc_auc']:.4f}")
            except Exception as e:
                st.warning(f"Churn model: {e}")

        # ── Train Forecast model ──────────────────────────────────────────────
        if train_forecast and "transaction_date" in df_clean.columns:
            progress.progress(80, text="Training Revenue Forecast model (Prophet)...")
            try:
                from ml.forecast.train import train as forecast_train
                rev_df = (df_clean.groupby("transaction_date")["amount"]
                          .sum().reset_index()
                          .rename(columns={"transaction_date":"date","amount":"revenue"}))
                _, metrics = forecast_train(rev_df, date_col="date", value_col="revenue")
                results["forecast"] = metrics
                progress.progress(95, text="Forecast model trained!")
            except Exception as e:
                st.warning(f"Forecast model: {e}")

        progress.progress(100, text="All done!")

        # ── Show results ──────────────────────────────────────────────────────
        st.markdown("### Training Results")
        r1, r2, r3 = st.columns(3)
        if "fraud" in results:
            r1.metric("Fraud Model AUC",     f"{results['fraud']['roc_auc']:.4f}")
        if "churn" in results:
            r2.metric("Churn Model AUC",     f"{results['churn']['roc_auc']:.4f}")
        if "forecast" in results and results["forecast"]:
            r3.metric("Forecast MAPE",       f"{results['forecast'].get('mape',0):.2%}")

        st.success("All models trained! Navigate to any analysis page to see results from your data.")

    # ── Export ─────────────────────────────────────────────────────────────────
    if is_data_loaded():
        st.markdown("---")
        st.subheader("Export Data")
        df_loaded = get_dataset()
        e1, e2, e3 = st.columns(3)
        with e1:
            st.download_button("Download CSV", df_loaded.to_csv(index=False),
                               file_name="intellibank_clean.csv", mime="text/csv")
        with e2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
                df_loaded.to_excel(w, index=False)
            st.download_button("Download Excel", buf.getvalue(),
                               file_name="intellibank_clean.xlsx")
        with e3:
            st.download_button("Download JSON", df_loaded.to_json(orient="records"),
                               file_name="intellibank_clean.json")

render_footer()
