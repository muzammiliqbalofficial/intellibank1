"""
Onboarding tour — shown to users on first login
"""
import streamlit as st

TOUR_STEPS = [
    {
        "title": "Welcome to IntelliBank!",
        "content": "Your AI-powered banking analytics platform. Let's take a quick tour of the key features.",
        "icon": "🏦",
    },
    {
        "title": "Data Upload",
        "content": "Start by uploading your banking data (CSV/Excel). IntelliBank will automatically profile and validate it.",
        "icon": "📤",
    },
    {
        "title": "Fraud Detection",
        "content": "Our XGBoost model detects fraudulent transactions with SHAP explainability — see exactly WHY a transaction was flagged.",
        "icon": "🚨",
    },
    {
        "title": "Customer Churn",
        "content": "Predict which customers are likely to leave. Get retention recommendations and risk segments.",
        "icon": "📉",
    },
    {
        "title": "Revenue Forecasting",
        "content": "Facebook Prophet forecasts revenue for the next 30/60/90 days with confidence intervals.",
        "icon": "📈",
    },
    {
        "title": "NLP Query",
        "content": "Ask questions in plain English or Urdu — IntelliBank converts them to SQL and returns results instantly.",
        "icon": "💬",
    },
    {
        "title": "You're all set!",
        "content": "Explore the sidebar to navigate between modules. Upload your dataset and all models train automatically.",
        "icon": "✅",
    },
]


def render_tour():
    if st.session_state.get("tour_completed", False):
        return

    if "tour_step" not in st.session_state:
        st.session_state.tour_step = 0

    step = st.session_state.tour_step
    if step >= len(TOUR_STEPS):
        st.session_state.tour_completed = True
        return

    current = TOUR_STEPS[step]
    total = len(TOUR_STEPS)

    with st.container():
        st.info(f"""
        **{current['icon']} {current['title']}** ({step + 1}/{total})

        {current['content']}
        """)

        progress = (step + 1) / total
        st.progress(progress)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            if st.button("Skip Tour"):
                st.session_state.tour_completed = True
                st.rerun()
        with col3:
            label = "Finish" if step == total - 1 else "Next →"
            if st.button(label, type="primary"):
                if step == total - 1:
                    st.session_state.tour_completed = True
                else:
                    st.session_state.tour_step = step + 1
                st.rerun()
