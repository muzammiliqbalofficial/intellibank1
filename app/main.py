"""
IntelliBank — Login Page
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64, os
import streamlit as st
from app.utils.session import init_session, login
from app.components.theme import load_css


def _logo_b64() -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

st.set_page_config(
    page_title="IntelliBank — Sign In",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
init_session()

if st.session_state.authenticated:
    st.switch_page("pages/Home.py")


@st.cache_resource
def initialize_database():
    from db.connection import init_db, SessionLocal
    from services.auth_service import AuthService
    from db.models import UserRole, User, Branch
    init_db()
    db = SessionLocal()
    try:
        if db.query(Branch).count() == 0:
            for b in [
                Branch(name="Karachi Main Branch", code="KHI-001", city="Karachi", region="Sindh"),
                Branch(name="Lahore Central",      code="LHR-001", city="Lahore",   region="Punjab"),
                Branch(name="Islamabad Capital",   code="ISB-001", city="Islamabad",region="Federal"),
                Branch(name="Peshawar Branch",     code="PEW-001", city="Peshawar", region="KPK"),
                Branch(name="Quetta Branch",       code="QTA-001", city="Quetta",   region="Balochistan"),
            ]:
                db.add(b)
            db.commit()
        if db.query(User).count() == 0:
            AuthService.create_user(db, "admin",   "admin@intellibank.com",   "admin123",   "System Admin",      UserRole.ADMIN)
            AuthService.create_user(db, "manager", "manager@intellibank.com", "manager123", "Bank Manager",      UserRole.BANK_MANAGER)
            AuthService.create_user(db, "analyst", "analyst@intellibank.com", "analyst123", "Business Analyst",  UserRole.BUSINESS_ANALYST)
    except Exception:
        db.rollback()
    finally:
        db.close()
    return True

initialize_database()

# ── Layout ────────────────────────────────────────────────────────────────────
left, mid, right = st.columns([1, 1.1, 1])

with left:
    st.markdown(f"""
    <div style="height:100vh; display:flex; flex-direction:column;
                justify-content:center; padding:40px 20px;">
        <div style="background:linear-gradient(135deg,#0d1b3e,#1a3a5c,#0d5c6e);
                    border-radius:20px; padding:40px 32px; color:white; height:85vh;
                    display:flex; flex-direction:column; justify-content:space-between;
                    box-shadow:0 12px 40px rgba(13,27,62,0.45);">
            <div>
                <h1 style="color:white; font-size:2.4rem; font-weight:800; margin:0;">IntelliBank</h1>
                <p style="color:rgba(255,255,255,0.75); font-size:1rem; margin-top:8px;">
                    AI-Powered Banking Data Analyst
                </p>
            </div>
            <div>
                <div style="margin-bottom:28px;">
                    <div style="display:flex; align-items:center; margin-bottom:16px;">
                        <div style="width:36px; height:36px; background:rgba(249,168,37,0.2);
                                    border-radius:8px; display:flex; align-items:center;
                                    justify-content:center; margin-right:12px; font-size:1.1rem;">🚨</div>
                        <div>
                            <div style="color:white; font-weight:600; font-size:0.9rem;">Fraud Detection</div>
                            <div style="color:rgba(255,255,255,0.6); font-size:0.78rem;">XGBoost + SHAP Explainability</div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; margin-bottom:16px;">
                        <div style="width:36px; height:36px; background:rgba(249,168,37,0.2);
                                    border-radius:8px; display:flex; align-items:center;
                                    justify-content:center; margin-right:12px; font-size:1.1rem;">📉</div>
                        <div>
                            <div style="color:white; font-weight:600; font-size:0.9rem;">Churn Prediction</div>
                            <div style="color:rgba(255,255,255,0.6); font-size:0.78rem;">Random Forest + Logistic Regression</div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; margin-bottom:16px;">
                        <div style="width:36px; height:36px; background:rgba(249,168,37,0.2);
                                    border-radius:8px; display:flex; align-items:center;
                                    justify-content:center; margin-right:12px; font-size:1.1rem;">📈</div>
                        <div>
                            <div style="color:white; font-weight:600; font-size:0.9rem;">Revenue Forecasting</div>
                            <div style="color:rgba(255,255,255,0.6); font-size:0.78rem;">Facebook Prophet Model</div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center;">
                        <div style="width:36px; height:36px; background:rgba(249,168,37,0.2);
                                    border-radius:8px; display:flex; align-items:center;
                                    justify-content:center; margin-right:12px; font-size:1.1rem;">💬</div>
                        <div>
                            <div style="color:white; font-weight:600; font-size:0.9rem;">NLP Query</div>
                            <div style="color:rgba(255,255,255,0.6); font-size:0.78rem;">Gemini AI · English & Urdu</div>
                        </div>
                    </div>
                </div>
                <div style="border-top:1px solid rgba(255,255,255,0.15); padding-top:20px;
                            color:rgba(255,255,255,0.5); font-size:0.75rem;">
                    Iqra University — Final Year Project 2026<br/>
                    Supervisor: Engr. Sidra Rehman
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with mid:
    st.markdown("<div style='height:5vh'></div>", unsafe_allow_html=True)
    col_pad1, col_logo, col_pad2 = st.columns([0.5, 3, 0.5])
    with col_logo:
        st.image("assets/logo.png", use_container_width=True)
    st.markdown("""
    <div style="text-align:center; margin-bottom:24px; margin-top:12px;">
        <h2 style="color:#0d1b3e; font-size:1.6rem; font-weight:700; margin:0;">Welcome Back</h2>
        <p style="color:#9e9e9e; margin:6px 0 0 0; font-size:0.9rem;">Sign in to your IntelliBank account</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter username or email")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            with st.spinner("Authenticating..."):
                try:
                    from db.connection import SessionLocal
                    from services.auth_service import AuthService
                    db = SessionLocal()
                    result = AuthService.authenticate(db, username, password)
                    db.close()
                    if result:
                        login(result["access_token"], result["user"])
                        st.switch_page("pages/Home.py")
                    else:
                        st.error("Invalid username or password.")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    st.markdown("""
    <div style="margin-top:24px; padding:16px 20px;
                background:#f8f9ff; border-radius:12px;
                border:1px solid #e8eaf6; text-align:center;">
        <div style="color:#9e9e9e; font-size:0.75rem; margin-bottom:8px; font-weight:600;
                    text-transform:uppercase; letter-spacing:0.05em;">Demo Credentials</div>
        <div style="display:flex; gap:8px; justify-content:center; flex-wrap:wrap;">
            <span style="background:#1a237e; color:white; padding:4px 12px;
                         border-radius:6px; font-size:0.78rem; font-weight:600;">
                admin / admin123
            </span>
            <span style="background:#1565c0; color:white; padding:4px 12px;
                         border-radius:6px; font-size:0.78rem; font-weight:600;">
                manager / manager123
            </span>
            <span style="background:#0277bd; color:white; padding:4px 12px;
                         border-radius:6px; font-size:0.78rem; font-weight:600;">
                analyst / analyst123
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; margin-top:20px; color:#bdbdbd; font-size:0.75rem;">
        🔒 Secured with bcrypt · JWT · Role-Based Access Control
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown("""
    <div style="height:100vh; display:flex; flex-direction:column;
                justify-content:center; padding:40px 20px;">
        <div style="background:#f8f9ff; border-radius:20px; padding:32px 28px;
                    height:85vh; display:flex; flex-direction:column;
                    justify-content:space-around; border:1px solid #e8eaf6;">
            <div style="text-align:center;">
                <div style="font-size:0.75rem; color:#9e9e9e; text-transform:uppercase;
                            letter-spacing:0.08em; font-weight:600; margin-bottom:16px;">
                    Model Performance
                </div>
                <div style="background:white; border-radius:12px; padding:16px;
                            margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                    <div style="color:#1a237e; font-weight:700; font-size:1.4rem;">97.2%</div>
                    <div style="color:#9e9e9e; font-size:0.78rem;">Fraud Detection AUC</div>
                </div>
                <div style="background:white; border-radius:12px; padding:16px;
                            margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                    <div style="color:#1565c0; font-weight:700; font-size:1.4rem;">89.1%</div>
                    <div style="color:#9e9e9e; font-size:0.78rem;">Churn Prediction AUC</div>
                </div>
                <div style="background:white; border-radius:12px; padding:16px;
                            box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                    <div style="color:#f57f17; font-weight:700; font-size:1.4rem;">4.2%</div>
                    <div style="color:#9e9e9e; font-size:0.78rem;">Revenue Forecast MAPE</div>
                </div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.75rem; color:#9e9e9e; text-transform:uppercase;
                            letter-spacing:0.08em; font-weight:600; margin-bottom:16px;">
                    System Features
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:8px; justify-content:center;">
                    <span style="background:#e8eaf6; color:#1a237e; padding:5px 12px;
                                 border-radius:20px; font-size:0.75rem; font-weight:500;">SHAP Explainability</span>
                    <span style="background:#e8eaf6; color:#1a237e; padding:5px 12px;
                                 border-radius:20px; font-size:0.75rem; font-weight:500;">Urdu NLP</span>
                    <span style="background:#e8eaf6; color:#1a237e; padding:5px 12px;
                                 border-radius:20px; font-size:0.75rem; font-weight:500;">Real-time Alerts</span>
                    <span style="background:#e8eaf6; color:#1a237e; padding:5px 12px;
                                 border-radius:20px; font-size:0.75rem; font-weight:500;">PDF Reports</span>
                    <span style="background:#e8eaf6; color:#1a237e; padding:5px 12px;
                                 border-radius:20px; font-size:0.75rem; font-weight:500;">REST API</span>
                    <span style="background:#e8eaf6; color:#1a237e; padding:5px 12px;
                                 border-radius:20px; font-size:0.75rem; font-weight:500;">Dark Mode</span>
                    <span style="background:#e8eaf6; color:#1a237e; padding:5px 12px;
                                 border-radius:20px; font-size:0.75rem; font-weight:500;">Drift Monitor</span>
                    <span style="background:#e8eaf6; color:#1a237e; padding:5px 12px;
                                 border-radius:20px; font-size:0.75rem; font-weight:500;">Docker Ready</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
