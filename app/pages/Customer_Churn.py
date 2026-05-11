import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.utils.session import require_auth, get_db_session
from app.utils.data_store import get_churn_df, is_data_loaded
from app.components.theme import load_css, apply_theme, render_page_header, render_footer
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="IntelliBank — Customer Churn", page_icon="📉", layout="wide", initial_sidebar_state="expanded")
load_css()
user = require_auth()
apply_theme(st.session_state.get("theme", "light"))
render_sidebar()

render_page_header("Customer Churn Prediction", "Random Forest + Logistic Regression ensemble with SHAP explainability", "📉")

tab1, tab2, tab3 = st.tabs(["Predict Customer", "Batch Analysis", "High-Risk Dashboard"])

# ─── Tab 1: Single Customer ───────────────────────────────────────────────────
with tab1:
    st.subheader("Predict Churn for a Single Customer")
    with st.form("churn_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            credit_score = st.slider("Credit Score", 300, 850, 650)
            age = st.number_input("Age", 18, 90, 42)
            tenure = st.slider("Years with Bank", 0, 10, 5)
        with c2:
            balance = st.number_input("Account Balance (PKR)", 0.0, 5000000.0, 125000.0, step=1000.0)
            num_products = st.selectbox("Number of Products", [1, 2, 3, 4])
            has_credit_card = st.radio("Has Credit Card?", ["Yes", "No"])
        with c3:
            is_active = st.radio("Is Active Member?", ["Yes", "No"])
            salary = st.number_input("Estimated Annual Salary (PKR)", 0.0, 5000000.0, 600000.0, step=10000.0)
            geography = st.selectbox("City", ["Karachi", "Lahore", "Islamabad", "Peshawar", "Quetta"])
            gender = st.selectbox("Gender", ["Male", "Female"])

        submit = st.form_submit_button("Predict Churn Risk", type="primary", use_container_width=True)

    if submit:
        with st.spinner("Running churn analysis..."):
            customer = {
                "credit_score": credit_score, "age": age, "tenure": tenure,
                "balance": balance, "num_products": num_products,
                "has_credit_card": 1 if has_credit_card == "Yes" else 0,
                "is_active_member": 1 if is_active == "Yes" else 0,
                "estimated_salary": salary,
                "geography": geography, "gender": gender,
            }
            try:
                from ml.churn.predict import predict_single
                result = predict_single(customer)

                col_gauge, col_info, col_shap = st.columns([1, 1, 2])

                with col_gauge:
                    prob = result["churn_probability"]
                    color = "#c62828" if prob >= 0.75 else "#f57f17" if prob >= 0.50 else "#2e7d32"
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=prob * 100,
                        title={"text": "Churn Risk"},
                        number={"suffix": "%", "font": {"color": color}},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": color},
                            "steps": [
                                {"range": [0, 25], "color": "#e8f5e9"},
                                {"range": [25, 50], "color": "#fff9c4"},
                                {"range": [50, 75], "color": "#fff3e0"},
                                {"range": [75, 100], "color": "#ffebee"},
                            ],
                        }
                    ))
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20),
                                      paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

                with col_info:
                    segment = result["risk_segment"]
                    color_map = {"High Risk": "error", "Medium Risk": "warning",
                                 "Low Risk": "info", "Loyal": "success"}
                    getattr(st, color_map.get(segment, "info"))(f"**{segment}**")
                    st.metric("Churn Probability", f"{result['churn_probability']:.1%}")
                    st.metric("Retention Priority", result["retention_urgency"])
                    st.metric("Confidence", f"{result['confidence']:.1%}")

                    if result["churn_probability"] >= 0.75:
                        st.warning("High churn risk — consider retention action for this customer.")

                with col_shap:
                    st.markdown("**Key Churn Drivers (SHAP)**")
                    top_factors = result.get("top_factors", [])
                    if top_factors:
                        shap_df = pd.DataFrame(top_factors[:8])
                        colors_shap = ["#ef5350" if v > 0 else "#42a5f5"
                                       for v in shap_df["shap_value"]]
                        fig_shap = go.Figure(go.Bar(
                            y=shap_df["feature"], x=shap_df["shap_value"],
                            orientation="h", marker_color=colors_shap,
                        ))
                        fig_shap.add_vline(x=0, line_dash="dash", line_color="grey")
                        fig_shap.update_layout(
                            height=300, margin=dict(l=0, r=20, t=10, b=0),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig_shap, use_container_width=True)

                        with st.expander("Plain Language Explanation"):
                            for f in top_factors[:5]:
                                st.markdown(f"- {f.get('readable', f['feature'])}")

            except FileNotFoundError:
                st.warning("Train the churn model first via Data Upload page.")
            except Exception as e:
                st.error(str(e))

# ─── Tab 2: Batch Analysis ────────────────────────────────────────────────────
with tab2:
    st.subheader("Batch Churn Prediction")

    # Use uploaded dataset from data_store if available
    if is_data_loaded():
        churn_df = get_churn_df()
        st.success(f"Using uploaded dataset — **{len(churn_df):,} unique customers** available for analysis.")
        use_uploaded = st.button("Analyze Uploaded Dataset", type="primary", key="analyze_uploaded_churn")
        st.markdown("---")
        st.markdown("*Or upload a different file below:*")
    else:
        churn_df = pd.DataFrame()
        use_uploaded = False
        st.info("No dataset uploaded yet. Go to **Data Upload** to upload your CSV, or upload a file below.")

    uploaded = st.file_uploader("Upload Customer CSV", type=["csv", "xlsx"], key="churn_batch")
    if uploaded:
        churn_df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
        st.info(f"File loaded: **{len(churn_df):,} customers**")
        use_uploaded = st.button("Analyze This File", type="primary", key="analyze_file_churn")

    if use_uploaded and not churn_df.empty:
        with st.spinner("Analyzing customers..."):
            try:
                from ml.churn.predict import predict_batch
                result_df = predict_batch(churn_df)

                high_risk = (result_df["will_churn"] == 1).sum()
                churn_rate = high_risk / len(result_df)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Customers", f"{len(result_df):,}")
                m2.metric("At-Risk (Churn)", f"{high_risk:,}")
                m3.metric("Predicted Churn Rate", f"{churn_rate:.1%}")
                m4.metric("Safe Customers", f"{len(result_df) - high_risk:,}")

                segment_counts = result_df["risk_segment"].value_counts().reset_index()
                segment_counts.columns = ["Segment", "Count"]
                color_map = {
                    "High Risk": "#c62828", "Medium Risk": "#f57f17",
                    "Low Risk": "#fdd835", "Loyal": "#2e7d32"
                }
                fig = px.bar(segment_counts, x="Segment", y="Count",
                             color="Segment",
                             color_discrete_map=color_map, title="Customer Risk Segments")
                fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

                # Churn probability distribution
                if "churn_probability" in result_df.columns:
                    fig2 = px.histogram(result_df, x="churn_probability", nbins=40,
                                        color_discrete_sequence=["#1a237e"],
                                        title="Churn Probability Distribution")
                    fig2.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Threshold")
                    fig2.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig2, use_container_width=True)

                st.dataframe(result_df.head(100), use_container_width=True)

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    st.download_button("Download Results (CSV)", result_df.to_csv(index=False),
                                       file_name="churn_analysis.csv")
                with col_e2:
                    try:
                        from services.report_service import generate_churn_report
                        pdf = generate_churn_report(result_df, {
                            "total": len(result_df), "high_risk": int(high_risk),
                            "churn_rate": float(churn_rate),
                            "revenue_at_risk": float(
                                result_df[result_df["will_churn"] == 1]["balance"].sum()
                                if "balance" in result_df.columns else 0
                            ),
                        })
                        st.download_button("Download PDF Report", pdf,
                                           file_name="churn_report.pdf", mime="application/pdf")
                    except Exception:
                        pass

            except FileNotFoundError:
                st.warning("Train the churn model first via Data Upload page.")
            except Exception as e:
                st.error(str(e))

# ─── Tab 3: High-Risk Dashboard ───────────────────────────────────────────────
with tab3:
    st.subheader("High-Risk Customer Dashboard")

    # First show from uploaded data if available
    if is_data_loaded():
        churn_df = get_churn_df()
        if "is_churned" in churn_df.columns:
            high_risk_df = churn_df[churn_df["is_churned"] == 1].copy()
            if not high_risk_df.empty:
                st.info(f"Showing **{len(high_risk_df):,}** churned customers from uploaded dataset.")
                display_cols = [c for c in ["customer_id", "age", "city", "credit_score",
                                            "account_balance", "tenure_years"] if c in high_risk_df.columns]
                st.dataframe(high_risk_df[display_cols].head(50), use_container_width=True, hide_index=True)

                # City breakdown
                if "city" in high_risk_df.columns:
                    city_churn = high_risk_df.groupby("city").size().reset_index(name="Churned")
                    fig = px.bar(city_churn, x="city", y="Churned", title="Churned Customers by City",
                                 color="Churned", color_continuous_scale="Reds")
                    fig.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("No churned customers in the uploaded dataset.")
        else:
            st.info("The uploaded dataset does not contain `is_churned` column.")
    else:
        db = get_db_session()
        try:
            from db.models import Customer
            at_risk = (
                db.query(Customer)
                .filter(Customer.churn_probability >= 0.6, Customer.is_churned == False)
                .order_by(Customer.churn_probability.desc())
                .limit(50)
                .all()
            )
        except Exception:
            at_risk = []
        finally:
            db.close()

        if at_risk:
            at_risk_data = [{
                "Customer": c.full_name,
                "Churn Probability": f"{c.churn_probability:.0%}",
                "Credit Score": c.credit_score,
                "Branch ID": c.branch_id,
            } for c in at_risk]
            st.dataframe(pd.DataFrame(at_risk_data), use_container_width=True, hide_index=True)
        else:
            st.info("No high-risk customers in the database. Upload and analyze customer data first.")

render_footer()
