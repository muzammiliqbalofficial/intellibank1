import streamlit as st
from app.utils.session import logout, current_language
from app.components.theme import theme_toggle

LABELS = {
    "en": {
        "nav": "Navigation",
        "home": "Dashboard",
        "upload": "Data Upload",
        "nlp": "NLP Query",
        "fraud": "Fraud Detection",
        "churn": "Customer Churn",
        "forecast": "Revenue Forecast",
        "branches": "Branch Analysis",
        "audit": "Audit Trail",
        "logout": "Logout",
        "theme": "Theme",
        "language": "Language",
    },
    "ur": {
        "nav": "نیویگیشن",
        "home": "ڈیش بورڈ",
        "upload": "ڈیٹا اپلوڈ",
        "nlp": "سوال پوچھیں",
        "fraud": "دھوکہ دہی کا پتہ",
        "churn": "گاہک چھوڑنا",
        "forecast": "آمدنی کی پیش گوئی",
        "branches": "شاخ تجزیہ",
        "audit": "آڈٹ ٹریل",
        "logout": "لاگ آؤٹ",
        "theme": "تھیم",
        "language": "زبان",
    }
}

# Pages visible per role — thesis section 4.3
ROLE_PAGES = {
    "admin": [
        ("🏠", "home",  "Home"),
        ("📋", "audit", "Audit_Trail"),
    ],
    "bank_manager": [
        ("🏠", "home", "Home"),
        ("💬", "nlp",  "NLP_Query"),
    ],
    "business_analyst": [
        ("🏠", "home",   "Home"),
        ("📤", "upload", "Data_Upload"),
        ("💬", "nlp",    "NLP_Query"),
        ("🚨", "fraud",  "Fraud_Detection"),
        ("📉", "churn",  "Customer_Churn"),
    ],
}

ROLE_LABELS = {
    "admin":            "🔴 Admin",
    "bank_manager":     "🟡 Bank Manager",
    "business_analyst": "🟢 Business Analyst",
}


def render_sidebar():
    lang = current_language()
    L    = LABELS.get(lang, LABELS["en"])
    user = st.session_state.get("user", {})
    role = user.get("role", "business_analyst")

    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 12px 0 4px 0;">
            <h2 style="color:white; margin:0; font-size:1.4rem;">🏦 IntelliBank</h2>
            <p style="color:rgba(255,255,255,0.6); font-size:0.72rem; margin:4px 0 0 0;">
                AI-Powered Banking Analyst
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        if user:
            st.markdown(f"""
            <div style="padding:6px 0 10px 0;">
                <div style="color:white; font-weight:600; font-size:0.95rem;">
                    {user.get('full_name', user.get('username', ''))}
                </div>
                <div style="color:rgba(255,255,255,0.65); font-size:0.78rem; margin-top:2px;">
                    {ROLE_LABELS.get(role, role)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        lang_col, theme_col = st.columns(2)
        with lang_col:
            new_lang = st.selectbox("Lang", ["EN", "UR"],
                                     index=0 if lang == "en" else 1,
                                     key="lang_selector", label_visibility="collapsed")
            if new_lang.lower() != lang:
                st.session_state.language = new_lang.lower()
                st.rerun()
        with theme_col:
            theme_toggle()

        st.divider()

        st.markdown(
            f"<div style='color:rgba(255,255,255,0.5);font-size:0.72rem;"
            f"text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;'>"
            f"{L['nav']}</div>",
            unsafe_allow_html=True
        )

        pages = ROLE_PAGES.get(role, ROLE_PAGES["business_analyst"])
        for icon, label_key, page_key in pages:
            label = L.get(label_key, label_key)
            if st.button(f"{icon}  {label}", key=f"nav_{page_key}", use_container_width=True):
                st.switch_page(f"pages/{page_key}.py")

        st.divider()

        if st.button("🚪  Logout", use_container_width=True, type="secondary"):
            logout()
