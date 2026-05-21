import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.utils.session import require_auth, get_db_session
from app.utils.data_store import get_fraud_df, is_data_loaded
from app.components.theme import load_css, apply_theme, render_page_header, render_footer
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="IntelliBank — Fraud Detection", page_icon="🚨", layout="wide", initial_sidebar_state="expanded")
load_css()
user = require_auth()
apply_theme(st.session_state.get("theme", "light"))
render_sidebar()

render_page_header("Fraud Detection", "XGBoost ML model with SHAP explainability and real-time alerts", "🚨")

tab1, tab2, tab3, tab4 = st.tabs(["Single Transaction", "Batch Analysis", "Alerts Dashboard", "Model Insights"])

# ─── Tab 1: Single Transaction ────────────────────────────────────────────────
with tab1:
    st.subheader("Analyze a Single Transaction")
    with st.form("single_fraud_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            amount = st.number_input("Transaction Amount (PKR)", min_value=0.0, value=5000.0, step=100.0)
            merchant_category = st.selectbox("Merchant Category",
                ["grocery", "electronics", "travel", "online", "atm", "restaurant", "healthcare"])
        with c2:
            transaction_type = st.selectbox("Transaction Type", ["debit", "credit", "transfer", "withdrawal"])
            location = st.text_input("Location", value="Karachi")
        with c3:
            hour = st.slider("Transaction Hour", 0, 23, 14)
            day_of_week = st.selectbox("Day of Week",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

        submit = st.form_submit_button("Analyze Transaction", type="primary", use_container_width=True)

    if submit:
        with st.spinner("Running fraud analysis..."):
            day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                       "Friday": 4, "Saturday": 5, "Sunday": 6}
            transaction = {
                "amount": amount, "merchant_category": merchant_category,
                "transaction_type": transaction_type, "location": location,
                "hour": hour, "day_of_week": day_map[day_of_week],
                "is_weekend": 1 if day_map[day_of_week] >= 5 else 0,
            }
            try:
                from ml.fraud.predict import predict_single
                result = predict_single(transaction)

                col_gauge, col_details = st.columns([1, 2])

                with col_gauge:
                    prob = result["fraud_probability"]
                    color = "#c62828" if prob >= 0.75 else "#f57f17" if prob >= 0.50 else "#2e7d32"
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=prob * 100,
                        title={"text": "Fraud Score"},
                        number={"suffix": "%", "font": {"color": color}},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": color},
                            "steps": [
                                {"range": [0, 40], "color": "#e8f5e9"},
                                {"range": [40, 70], "color": "#fff3e0"},
                                {"range": [70, 100], "color": "#ffebee"},
                            ],
                            "threshold": {"line": {"color": "black", "width": 3}, "value": 75},
                        }
                    ))
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20),
                                      paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

                with col_details:
                    if result["is_fraud"]:
                        st.error(f"**FRAUD DETECTED** — Risk Level: {result['risk_level']}")
                    else:
                        st.success(f"**Transaction Appears Legitimate** — Risk Level: {result['risk_level']}")

                    st.metric("Fraud Probability", f"{result['fraud_probability']:.1%}")
                    st.metric("Confidence", f"{result['confidence']:.1%}")

                st.markdown("#### Why was this flagged? (SHAP Explanation)")
                top_features = result.get("top_features", [])
                if top_features:
                    shap_df = pd.DataFrame(top_features[:8])
                    colors_shap = ["#ef5350" if v > 0 else "#42a5f5"
                                   for v in shap_df["shap_value"]]
                    fig_shap = go.Figure(go.Bar(
                        y=shap_df["feature"],
                        x=shap_df["shap_value"],
                        orientation="h",
                        marker_color=colors_shap,
                        text=[f"{v:+.4f}" for v in shap_df["shap_value"]],
                        textposition="outside",
                    ))
                    fig_shap.update_layout(
                        height=300, margin=dict(l=0, r=60, t=20, b=0),
                        xaxis_title="SHAP Value (impact on fraud score)",
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    )
                    fig_shap.add_vline(x=0, line_dash="dash", line_color="grey")
                    st.plotly_chart(fig_shap, use_container_width=True)
                    st.caption("Red bars = increase fraud risk | Blue bars = decrease fraud risk")

            except FileNotFoundError:
                st.warning("Fraud model not trained yet. Please upload data and train on the Data Upload page.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ─── Tab 2: Batch Analysis ────────────────────────────────────────────────────
with tab2:
    st.subheader("Batch Transaction Analysis")

    # Use uploaded dataset from data_store if available
    if is_data_loaded():
        fraud_df = get_fraud_df()
        st.success(f"Using uploaded dataset — **{len(fraud_df):,} transactions** available for analysis.")
        use_uploaded = st.button("Analyze Uploaded Dataset", type="primary", key="analyze_uploaded_fraud")
        st.markdown("---")
        st.markdown("*Or upload a different file below:*")
    else:
        fraud_df = pd.DataFrame()
        use_uploaded = False
        st.info("No dataset uploaded yet. Go to **Data Upload** to upload your CSV, or upload a file below.")

    uploaded = st.file_uploader("Upload Transactions CSV", type=["csv", "xlsx"], key="fraud_batch")
    if uploaded:
        fraud_df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
        st.info(f"File loaded: **{len(fraud_df):,} transactions**")
        use_uploaded = st.button("Analyze This File", type="primary", key="analyze_file_fraud")

    if use_uploaded and not fraud_df.empty:
        with st.spinner(f"Analyzing {len(fraud_df):,} transactions..."):
            try:
                from ml.fraud.predict import predict_batch
                result_df = predict_batch(fraud_df)

                fraud_count = (result_df["is_fraud_predicted"] == 1).sum()
                fraud_rate = fraud_count / len(result_df)

                m1, m2, m3 = st.columns(3)
                m1.metric("Total Analyzed", f"{len(result_df):,}")
                m2.metric("Fraudulent", f"{fraud_count:,}", delta=f"{fraud_rate:.1%}")
                m3.metric("Legitimate", f"{len(result_df) - fraud_count:,}")

                fig = px.histogram(result_df, x="fraud_probability", nbins=50,
                                   color_discrete_sequence=["#1a237e"],
                                   title="Fraud Score Distribution")
                fig.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Threshold")
                fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(result_df.head(100), use_container_width=True)

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    st.download_button("Download Results (CSV)", result_df.to_csv(index=False),
                                       file_name="fraud_analysis.csv", mime="text/csv")
                with col_e2:
                    try:
                        from services.report_service import generate_fraud_report
                        pdf = generate_fraud_report(result_df, {
                            "total": len(result_df), "fraud_count": int(fraud_count),
                            "fraud_rate": float(fraud_rate),
                            "total_amount_at_risk": float(
                                result_df[result_df["is_fraud_predicted"] == 1]["amount"].sum()
                                if "amount" in result_df.columns else 0
                            ),
                        })
                        st.download_button("Download PDF Report", pdf,
                                           file_name="fraud_report.pdf", mime="application/pdf")
                    except Exception:
                        pass

            except FileNotFoundError:
                st.warning("Train the fraud model first (Data Upload page).")
            except Exception as e:
                st.error(str(e))

# ─── Tab 3: Alerts Dashboard ─────────────────────────────────────────────────
with tab3:
    st.subheader("Live Fraud Alerts")
    st.markdown("""
    <div class="live-alert-banner" style="background:#ffebee;border-left:4px solid #c62828;padding:10px 16px;border-radius:4px;margin-bottom:16px;">
        🔴 Real-Time Monitoring Active
    </div>
    """, unsafe_allow_html=True)

    db = get_db_session()
    try:
        from db.models import FraudAlert
        alerts = (
            db.query(FraudAlert)
            .order_by(FraudAlert.created_at.desc())
            .limit(50)
            .all()
        )
    except Exception:
        alerts = []
    finally:
        db.close()

    if alerts:
        alert_data = [{
            "ID": a.id,
            "Fraud Score": f"{a.fraud_score:.0%}",
            "Resolved": "✅" if a.is_resolved else "🔴",
            "Created": str(a.created_at)[:16] if a.created_at else "N/A",
        } for a in alerts]
        st.dataframe(pd.DataFrame(alert_data), use_container_width=True, hide_index=True)
    else:
        st.info("No fraud alerts in the database yet. Analyze transactions to generate alerts.")

# ─── Tab 4: Model Insights ────────────────────────────────────────────────────
with tab4:
    st.subheader("Model Verification — How We Know It Works")
    try:
        import json
        from pathlib import Path
        metrics_path = Path("ml/fraud/artifacts/fraud_metrics.json")
        if not metrics_path.exists():
            st.info("Train the model first (Data Upload page) to see verification metrics.")
        else:
            with open(metrics_path) as f:
                m = json.load(f)

            # ── Methodology note ──────────────────────────────────────────────
            n_train = m.get("n_train", 0)
            n_test  = m.get("n_test",  0)
            st.info(
                f"**Verification methodology:** The model was trained on **{n_train:,}** transactions "
                f"and evaluated on a completely separate **{n_test:,}** test set "
                f"(20% hold-out — the model never saw these during training). "
                f"All metrics below come from this independent test set."
            )

            # ── KPI row ───────────────────────────────────────────────────────
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("ROC-AUC",       f"{m.get('roc_auc', 0):.4f}",
                      help="1.0 = perfect, 0.5 = random guessing")
            k2.metric("Avg Precision", f"{m.get('avg_precision', 0):.4f}",
                      help="Area under Precision-Recall curve")
            cr = m.get("classification_report", {})
            k3.metric("Fraud Recall",
                      f"{cr.get('1', {}).get('recall', 0):.1%}",
                      help="% of actual fraud cases that were caught")
            k4.metric("Fraud Precision",
                      f"{cr.get('1', {}).get('precision', 0):.1%}",
                      help="% of fraud alerts that were real fraud")

            st.markdown("---")

            col_cm, col_roc = st.columns(2)

            # ── Confusion Matrix ──────────────────────────────────────────────
            with col_cm:
                st.markdown("#### Confusion Matrix")
                st.caption("Rows = Actual label · Columns = Predicted label")
                cm = m.get("confusion_matrix")
                if cm:
                    tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
                    fig_cm = go.Figure(go.Heatmap(
                        z=[[tn, fp], [fn, tp]],
                        x=["Predicted Legit", "Predicted Fraud"],
                        y=["Actual Legit",    "Actual Fraud"],
                        text=[[f"TN\n{tn}", f"FP\n{fp}"],
                              [f"FN\n{fn}", f"TP\n{tp}"]],
                        texttemplate="%{text}",
                        textfont=dict(size=16, color="white"),
                        colorscale=[[0, "#1a237e"], [0.5, "#1565c0"], [1, "#c62828"]],
                        showscale=False,
                    ))
                    fig_cm.update_layout(
                        height=280, margin=dict(l=0, r=0, t=10, b=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig_cm, use_container_width=True,
                                    config={"displayModeBar": False})
                    st.caption(
                        f"✅ **{tp} fraud correctly caught** (True Positives)  "
                        f"· ❌ {fn} fraud missed (False Negatives)  "
                        f"· ⚠️ {fp} false alarms (False Positives)"
                    )

            # ── ROC Curve ─────────────────────────────────────────────────────
            with col_roc:
                st.markdown("#### ROC Curve")
                st.caption("Closer the curve is to top-left corner, better the model")
                roc = m.get("roc_curve")
                if roc:
                    auc_val = m.get("roc_auc", 0)
                    fig_roc = go.Figure()
                    fig_roc.add_trace(go.Scatter(
                        x=roc["fpr"], y=roc["tpr"],
                        mode="lines",
                        name=f"Fraud Model (AUC={auc_val:.3f})",
                        line=dict(color="#c62828", width=2.5),
                        fill="tozeroy", fillcolor="rgba(198,40,40,0.08)",
                    ))
                    fig_roc.add_trace(go.Scatter(
                        x=[0, 1], y=[0, 1],
                        mode="lines", name="Random (AUC=0.5)",
                        line=dict(color="#9e9e9e", width=1.5, dash="dash"),
                    ))
                    fig_roc.update_layout(
                        height=280, margin=dict(l=0, r=0, t=10, b=0),
                        xaxis_title="False Positive Rate",
                        yaxis_title="True Positive Rate",
                        legend=dict(orientation="h", y=0.05, x=0.4),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(gridcolor="#f0f0f0"),
                        yaxis=dict(gridcolor="#f0f0f0"),
                    )
                    st.plotly_chart(fig_roc, use_container_width=True,
                                    config={"displayModeBar": False})

            # ── Per-class Report ──────────────────────────────────────────────
            if cr:
                st.markdown("---")
                st.markdown("#### Detailed Classification Report (Test Set)")
                report_data = {
                    "Class":     ["Legitimate (0)", "Fraudulent (1)", "Weighted Avg"],
                    "Precision": [f"{cr.get('0',{}).get('precision',0):.1%}",
                                  f"{cr.get('1',{}).get('precision',0):.1%}",
                                  f"{cr.get('weighted avg',{}).get('precision',0):.1%}"],
                    "Recall":    [f"{cr.get('0',{}).get('recall',0):.1%}",
                                  f"{cr.get('1',{}).get('recall',0):.1%}",
                                  f"{cr.get('weighted avg',{}).get('recall',0):.1%}"],
                    "F1-Score":  [f"{cr.get('0',{}).get('f1-score',0):.1%}",
                                  f"{cr.get('1',{}).get('f1-score',0):.1%}",
                                  f"{cr.get('weighted avg',{}).get('f1-score',0):.1%}"],
                    "Support":   [int(cr.get('0',{}).get('support',0)),
                                  int(cr.get('1',{}).get('support',0)),
                                  int(cr.get('weighted avg',{}).get('support',0))],
                }
                st.dataframe(pd.DataFrame(report_data), use_container_width=True, hide_index=True)
                st.caption(
                    "**Precision** = when model says fraud, how often is it right?  "
                    "**Recall** = of all real fraud, how many did we catch?  "
                    "**F1** = balance between precision and recall."
                )

    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")

render_footer()
