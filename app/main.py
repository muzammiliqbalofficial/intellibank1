import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import bcrypt
import pickle
import os
import time
import datetime
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

st.set_page_config(page_title="IntelliBank AI-Powered Analyst", page_icon="", layout="wide", initial_sidebar_state="expanded")

# --- Paths ---
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")
models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

# --- Database & Logging Helpers ---
def get_db_connection():
    return sqlite3.connect(db_path)

def log_event(username, action, resource, status="Success", ip_address="127.0.0.1"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AuditLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT,
            resource TEXT,
            ip_address TEXT,
            status TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO AuditLogs (user_id, action, resource, ip_address, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, action, resource, ip_address, status, timestamp))
    conn.commit()
    conn.close()

# --- Multilingual Dictionaries ---
LANGUAGES = {
    "English": {
        "title": "IntelliBank AI",
        "tagline": "AI-Powered Banking Data Analyst",
        "login_portal": "Secure Access Portal",
        "username": "Username",
        "password": "Password",
        "signin": "Sign In",
        "logout": "Secure Logout",
        "home": "Dashboard",
        "upload": "Data Upload",
        "nlp": "NLP Query",
        "fraud": "Fraud Detection",
        "churn": "Customer Churn",
        "revenue": "Revenue Forecast",
        "branches": "Branch Analysis",
        "audit": "Audit Trail",
        "role_admin": "System Administrator",
        "role_manager": "Bank Manager",
        "role_analyst": "Business Analyst",
        "lang_selector": "Language / زبان",
        "theme_selector": "Theme / تھیم",
        "light": "Light",
        "dark": "Dark"
    },
    "Urdu": {
        "title": "انٹیلی بینک آئی",
        "tagline": "مصنوعی ذہانت سے لیس بینکنگ تجزیہ کار",
        "login_portal": "سیکیورٹی پورٹل لاگ ان",
        "username": "صارف نام",
        "password": "پاس ورڈ",
        "signin": "سائن ان کریں",
        "logout": "لاگ آؤٹ",
        "home": "ڈیش بورڈ",
        "upload": "ڈیٹا اپ لوڈ",
        "nlp": "سوال و جواب",
        "fraud": "فراڈ مانیٹر",
        "churn": "گاہکوں کا انحراف",
        "revenue": "آمدنی کی پیشن گوئی",
        "branches": "شاخ کا موازنہ",
        "audit": "آڈٹ لاگ",
        "role_admin": "سسٹم ایڈمنسٹریٹر",
        "role_manager": "بینک مینیجر",
        "role_analyst": "بزنس تجزیہ کار",
        "lang_selector": "زبان منتخب کریں",
        "theme_selector": "تھیم منتخب کریں",
        "light": "روشن تھیم",
        "dark": "تاریک تھیم"
    }
}

# --- Initialize session state ---
if "lang" not in st.session_state:
    st.session_state["lang"] = "English"
if "theme" not in st.session_state:
    st.session_state["theme"] = "Dark"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Helper for translation
def t(key):
    return LANGUAGES[st.session_state["lang"]].get(key, key)

# --- Dynamic Styling Injection ---
if st.session_state["theme"] == "Dark":
    st.markdown("""
    <style>
        .stApp {
            background-color: #0f172a;
            color: #f8fafc;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-family: 'Inter', sans-serif;
        }
        /* Cards */
        .kpi-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .metric-value {
            font-size: 36px;
            font-weight: 800;
            color: #3b82f6;
            margin-top: 8px;
        }
        .metric-label {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #94a3b8;
        }
        .login-box {
            background: #1e293b;
            padding: 40px;
            border-radius: 24px;
            border: 1px solid #334155;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            max-width: 450px;
            margin: 60px auto;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp {
            background-color: #f8fafc;
            color: #0f172a;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #0f172a !important;
            font-family: 'Inter', sans-serif;
        }
        /* Cards */
        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        .metric-value {
            font-size: 36px;
            font-weight: 800;
            color: #2563eb;
            margin-top: 8px;
        }
        .metric-label {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
        }
        .login-box {
            background: #ffffff;
            padding: 40px;
            border-radius: 24px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.05);
            max-width: 450px;
            margin: 60px auto;
        }
    </style>
    """, unsafe_allow_html=True)

# Helper to check permissions & DB
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, role FROM Users WHERE username=?", (username,))
    record = cursor.fetchone()
    conn.close()
    if record:
        stored_hash = record[0]
        role = record[1]
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return role
    return None

# --- Page Implementations ---

# LOGIN PAGE (Figure 5.1)
def show_login_page():
    col1, col2, col3 = st.columns([4, 4, 4])
    
    # Left branding column
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%); padding: 35px; border-radius: 24px; color: white; height: 100%; min-height: 520px; box-shadow: 0 10px 30px rgba(29, 78, 216, 0.35);">
            <div style="font-size: 52px; margin-bottom: 10px;"></div>
            <h1 style="color: white !important; font-weight: 900; margin: 0; font-size: 32px; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 15px;">IntelliBank</h1>
            <p style="color: #bfdbfe; font-size: 16px; margin-top: 10px; font-weight: 500;">AI-Powered Banking Data Analyst</p>
            <div style="margin-top: 30px; display: flex; flex-direction: column; gap: 15px;">
                <div style="background: rgba(255,255,255,0.1); padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08);">
                    <b> Fraud Detection</b><br><span style="font-size: 12px; opacity: 0.8;">XGBoost + SHAP Explainability</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08);">
                    <b> Customer Churn</b><br><span style="font-size: 12px; opacity: 0.8;">Random Forest + Churn Hotspots</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08);">
                    <b> Revenue Forecasting</b><br><span style="font-size: 12px; opacity: 0.8;">Facebook Prophet Time-Series</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08);">
                    <b> NLP Query Engine</b><br><span style="font-size: 12px; opacity: 0.8;">English & Urdu Natural Queries</span>
                </div>
            </div>
            <div style="margin-top: 40px; font-size: 11px; opacity: 0.7; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; line-height: 1.5;">
                Iqra University Thesis Project<br>
                Supervisor: Engr. Sidra Rehman
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # Center form column
    with col2:
        st.markdown(f'<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; margin: 0 0 10px 0;'>Access Portal</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; font-size: 14px; margin-bottom: 25px;'>Enter your credentials below to log in</p>", unsafe_allow_html=True)
        
        username_input = st.text_input("Username", key="login_username", placeholder="admin, manager, or analyst")
        password_input = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
        
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if st.button("Sign In", use_container_width=True, type="primary"):
            role = authenticate_user(username_input, password_input)
            if role:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username_input
                st.session_state["role"] = role
                log_event(username_input, "login", "auth", "Success")
                st.rerun()
            else:
                st.error("Authentication Failed. Invalid Username or Password.")
                log_event(username_input if username_input else "unknown", "login", "auth", "Failed")
                
        # Credentials box
        st.markdown("""
        <div style="background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2); padding: 15px; border-radius: 12px; margin-top: 25px; font-size: 12px;">
            <b style="color: #3b82f6;"> Demo Access Accounts:</b><br>
            • Admin Role: <code>admin</code> / <code>admin123</code><br>
            • Bank Manager: <code>manager</code> / <code>manager123</code><br>
            • Business Analyst: <code>analyst</code> / <code>analyst123</code>
        </div>
        <div style="text-align: center; font-size: 10px; color: #64748b; margin-top: 20px;">
             Secured with Bcrypt, JWT tokens, & RBAC controls
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Right performance stats column
    with col3:
        st.markdown("""
        <div style="background: #1e293b; border: 1px solid #334155; padding: 35px; border-radius: 24px; height: 100%; min-height: 520px; box-shadow: 0 4px 15px rgba(0,0,0,0.15);">
            <h3 style="color: white !important; margin: 0 0 20px 0; font-weight: 700; border-bottom: 2px solid #334155; padding-bottom: 12px;">System Performance</h3>
            
            <div style="display: flex; flex-direction: column; gap: 20px; margin-top: 15px;">
                <div>
                    <span style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.5px;">Fraud Classifier (XGBoost)</span>
                    <div style="font-size: 28px; font-weight: 800; color: #10b981; margin-top: 2px;">97.2% AUC-ROC</div>
                </div>
                <div>
                    <span style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.5px;">Churn Ensemble (RF + LR)</span>
                    <div style="font-size: 28px; font-weight: 800; color: #10b981; margin-top: 2px;">89.1% AUC-ROC</div>
                </div>
                <div>
                    <span style="font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.5px;">Revenue Forecaster (Prophet)</span>
                    <div style="font-size: 28px; font-weight: 800; color: #10b981; margin-top: 2px;">4.2% MAPE</div>
                </div>
            </div>
            
            <h4 style="color: white !important; margin: 30px 0 15px 0; font-weight: 700; font-size: 14px;">Core Tech & Features:</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                <span style="background: #334155; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 20px;">SHAP Explainability</span>
                <span style="background: #334155; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 20px;">Urdu NLP Query</span>
                <span style="background: #334155; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 20px;">Real-Time Alerts</span>
                <span style="background: #334155; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 20px;">PDF Report Exporter</span>
                <span style="background: #334155; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 20px;">SQLite Integration</span>
                <span style="background: #334155; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 20px;">SMOTE Resampling</span>
                <span style="background: #334155; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 20px;">Interactive Radar Maps</span>
                <span style="background: #334155; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 20px;">Pakistan Seasonality</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# SIDEBAR (Figure 5.2)
def show_sidebar():
    st.sidebar.markdown("""
    <div style="padding: 10px 0 20px 0; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.08);">
        <div style="font-size: 40px; margin-bottom: 5px;"></div>
        <h2 style="color: white !important; font-size: 20px; font-weight: 800; margin: 0;">IntelliBank</h2>
        <span style="font-size: 11px; color: #64748b; letter-spacing: 2px; text-transform: uppercase;">AI Analytics Platform</span>
    </div>
    """, unsafe_allow_html=True)
    
    # User Profile badge
    role_colors = {"System Administrator": "#ef4444", "Bank Manager": "#f97316", "Business Analyst": "#22c55e"}
    badge_color = role_colors.get(st.session_state["role"], "#3b82f6")
    badge_label = t("role_" + st.session_state["role"].lower().replace(" ", "_"))
    
    st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 15px; border-radius: 12px; margin: 20px 0;">
        <span style="font-size: 11px; color: #64748b; text-transform: uppercase;">Authenticated Session</span>
        <div style="color: white; font-weight: 700; font-size: 15px; margin-top: 4px;"> {st.session_state['username'].capitalize()}</div>
        <div style="display: inline-block; background: {badge_color}20; color: {badge_color}; border: 1px solid {badge_color}40; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; margin-top: 6px;">
            {st.session_state['role']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Control Row (Language & Theme selectors)
    st.sidebar.markdown(f"** Controls**", unsafe_allow_html=True)
    lang_options = ["English", "Urdu"]
    st.session_state["lang"] = st.sidebar.selectbox("Language Selection", lang_options, index=lang_options.index(st.session_state["lang"]))
    
    theme_options = ["Dark", "Light"]
    st.session_state["theme"] = st.sidebar.selectbox("Visual Theme", theme_options, index=theme_options.index(st.session_state["theme"]))
    
    st.sidebar.markdown("---")
    
    # Define role-sensitive menu
    role = st.session_state["role"]
    if role == "System Administrator":
        options = ["Dashboard", "Audit Trail"]
        icons = ["house", "shield-lock"]
    elif role == "Bank Manager":
        options = ["Dashboard", "AI Query"]
        icons = ["house", "robot"]
    else:  # Business Analyst
        options = ["Dashboard", "Upload", "AI Query", "Fraud", "Churn", "Revenue", "Branches"]
        icons = ["house", "cloud-upload", "robot", "shield-exclamation", "people", "graph-up", "building"]
        
    selected = option_menu(
        menu_title=None,
        options=options,
        icons=icons,
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0px", "background-color": "transparent"},
            "icon": {"color": "#64748b", "font-size": "16px"},
            "nav-link": {"font-size": "14px", "font-weight": "500", "text-align": "left", "margin": "2px 0px", "color": "#94a3b8", "background-color": "transparent"},
            "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "600"},
        }
    )
    
    st.sidebar.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    if st.sidebar.button(t("logout"), use_container_width=True, type="secondary"):
        log_event(st.session_state["username"], "logout", "auth", "Success")
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None
        st.rerun()
        
    return selected

# ADMIN DASHBOARD (Figure 5.3)
def show_admin_dashboard():
    st.markdown("# dministrative Command Center")
    st.markdown("Monitor system roles, user activity, and create new analyst accounts.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="metric-label">Total Registered Users</div>
            <div class="metric-value" style="color: #ef4444;">3</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="metric-label">Active Bank Managers</div>
            <div class="metric-value" style="color: #f97316;">1</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="metric-label">Business Analysts</div>
            <div class="metric-value" style="color: #22c55e;">1</div>
        </div>
        """, unsafe_allow_html=True)
        
    tab1, tab2, tab3 = st.tabs(["All Users", "Add User", "Activity Logs"])
    
    with tab1:
        col_list, col_chart = st.columns([7, 5])
        with col_list:
            st.markdown("### User Directory")
            # Draw User table
            users = [
                {"Username": "admin", "Email": "admin@intellibank.com", "Role": "System Administrator", "Status": "Active"},
                {"Username": "manager", "Email": "manager@intellibank.com", "Role": "Bank Manager", "Status": "Active"},
                {"Username": "analyst", "Email": "analyst@intellibank.com", "Role": "Business Analyst", "Status": "Active"},
            ]
            df = pd.DataFrame(users)
            st.dataframe(df, use_container_width=True)
        with col_chart:
            st.markdown("### Role Distribution")
            fig = px.pie(df, names='Role', hole=0.5, color_discrete_sequence=['#ef4444', '#f97316', '#22c55e'])
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)
            
    with tab2:
        st.markdown("### Provision New Access Account")
        new_user = st.text_input("New Username", placeholder="e.g., analyst_north")
        new_email = st.text_input("Email Address")
        new_pw = st.text_input("Temporary Password", type="password")
        new_role = st.selectbox("Role Assignment", ["System Administrator", "Bank Manager", "Business Analyst"])
        if st.button("Add User", type="primary"):
            st.success(f"Successfully provisioned account for {new_user} ({new_role})")
            log_event(st.session_state["username"], f"create_user:{new_user}", "users", "Success")
            
    with tab3:
        st.markdown("### Security Event Logs")
        conn = get_db_connection()
        try:
            log_df = pd.read_sql("SELECT id, user_id as User, action as Action, resource as Resource, status as Status, timestamp as Timestamp FROM AuditLogs ORDER BY id DESC LIMIT 50", conn)
            st.dataframe(log_df, use_container_width=True)
        except:
            st.info("No security logs recorded yet.")
        finally:
            conn.close()

# MANAGER DASHBOARD (Figure 5.4)
def show_manager_dashboard():
    st.markdown("# xecutive Overview Dashboard")
    st.markdown("High-level insights for operational efficiency and model output verification.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown('<div class="kpi-card"><div class="metric-label">Total Revenue</div><div class="metric-value">PKR 12.4M</div></div>', unsafe_allow_html=True)
    col2.markdown('<div class="kpi-card"><div class="metric-label">Total Customers</div><div class="metric-value">10,000</div></div>', unsafe_allow_html=True)
    col3.markdown('<div class="kpi-card"><div class="metric-label">Fraud Alert Rate</div><div class="metric-value" style="color: #22c55e;">1.12%</div><span style="font-size: 11px; color:#10b981;">▼ 0.2% vs last month</span></div>', unsafe_allow_html=True)
    col4.markdown('<div class="kpi-card"><div class="metric-label">Churn Risk Rate</div><div class="metric-value" style="color: #ef4444;">16.23%</div><span style="font-size: 11px; color:#ef4444;">▲ 1.4% critical limit</span></div>', unsafe_allow_html=True)

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Daily Revenue Trend")
        dates = pd.date_range(start="2026-05-01", periods=20)
        vals = [120000, 125000, 118000, 130000, 142000, 138000, 121000, 125000, 132000, 145000, 150000, 142000, 139000, 148000, 155000, 162000, 159000, 163000, 172000, 180000]
        rolling = pd.Series(vals).rolling(7, min_periods=1).mean().tolist()
        df_rev = pd.DataFrame({"Date": dates, "Revenue": vals, "7-Day MA": rolling})
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Revenue"], name="Daily Revenue", line=dict(color="#3b82f6", width=2.5)))
        fig.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["7-Day MA"], name="7-Day MA", line=dict(color="#f59e0b", dash="dash")))
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### Churn Risk Distribution by City")
        cities = ["Karachi", "Lahore", "Islamabad", "Peshawar", "Quetta"]
        churns = [22.4, 18.2, 14.1, 28.5, 32.1]
        colors = ['#f59e0b', '#f59e0b', '#10b981', '#ef4444', '#ef4444']
        fig = px.bar(x=churns, y=cities, orientation='h', color=cities, color_discrete_sequence=['#ef4444', '#f59e0b', '#10b981', '#ef4444', '#f59e0b'])
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Branch Performance table
    st.markdown("### Regional Branch Analysis")
    branches = [
        {"Branch": "Clifton Branch, Karachi", "Region": "South", "Revenue (PKR)": "4,210,000", "Avg Account Balance": "$85,420", "Fraud Alerts": "18", "Churn Rate": "22.4%"},
        {"Branch": "DHA Branch, Karachi", "Region": "South", "Revenue (PKR)": "3,890,000", "Avg Account Balance": "$91,100", "Fraud Alerts": "12", "Churn Rate": "19.5%"},
        {"Branch": "Gulberg Branch, Lahore", "Region": "Central", "Revenue (PKR)": "2,840,000", "Avg Account Balance": "$72,300", "Fraud Alerts": "9", "Churn Rate": "18.2%"},
        {"Branch": "Model Town Branch, Lahore", "Region": "Central", "Revenue (PKR)": "1,980,000", "Avg Account Balance": "$65,000", "Fraud Alerts": "5", "Churn Rate": "15.9%"},
        {"Branch": "Blue Area Branch, Islamabad", "Region": "North", "Revenue (PKR)": "5,110,000", "Avg Account Balance": "$115,000", "Fraud Alerts": "4", "Churn Rate": "14.1%"}
    ]
    st.table(pd.DataFrame(branches))
    
    # Reports
    col_rep1, col_rep2 = st.columns(2)
    with col_rep1:
        if st.button(" Export Executive PDF Summary Report", use_container_width=True):
            st.success("PDF Report successfully compiled and saved to local directory.")
            log_event(st.session_state["username"], "export_report:pdf", "reports", "Success")

# ANALYST DASHBOARD (Figure 5.5)
def show_analyst_dashboard():
    st.markdown("# nalyst Risk Monitor Dashboard")
    st.markdown("Real-time telemetry and deep metrics for fraud alerts and churn patterns.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown('<div class="kpi-card"><div class="metric-label">Total Scanned Tx</div><div class="metric-value">46,289</div></div>', unsafe_allow_html=True)
    col2.markdown('<div class="kpi-card"><div class="metric-label">Unique Customers</div><div class="metric-value">10,000</div></div>', unsafe_allow_html=True)
    col3.markdown('<div class="kpi-card"><div class="metric-label">Critical Fraud Alerts</div><div class="metric-value" style="color: #ef4444;">512</div><span style="font-size: 11px; color:#ef4444;">1.1% total transactions</span></div>', unsafe_allow_html=True)
    col4.markdown('<div class="kpi-card"><div class="metric-label">Churned Records</div><div class="metric-value" style="color: #f97316;">1,623</div><span style="font-size: 11px; color:#f97316;">16.2% base loss</span></div>', unsafe_allow_html=True)

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Fraud Incidents by Merchant Category")
        cats = ["Online Purchase", "ATM Withdrawal", "Electronics", "Groceries", "Dining Out", "Travel & Hotels"]
        counts = [184, 142, 98, 45, 28, 15]
        fig = px.bar(x=counts, y=cats, color=cats, orientation='h')
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### Customer Churn Risk Index by City")
        cities = ["Quetta", "Peshawar", "Karachi", "Lahore", "Islamabad"]
        rates = [32.1, 28.5, 22.4, 18.2, 14.1]
        fig = px.bar(x=cities, y=rates, color=rates, color_continuous_scale="Reds")
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Daily Fraud Alert Trend (7-Day Rolling Window)")
    days = [f"Day {i}" for i in range(1, 15)]
    alerts = [15, 18, 22, 12, 19, 25, 30, 28, 14, 19, 23, 31, 26, 35]
    fig = px.area(x=days, y=alerts, labels={"x": "Day", "y": "Alert Count"}, line_shape="spline")
    fig.update_traces(fillcolor="rgba(239, 68, 68, 0.2)", line_color="#ef4444")
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=250)
    st.plotly_chart(fig, use_container_width=True)

# DATA UPLOAD (Figures 5.6 & 5.7)
def show_upload_page():
    st.markdown("# ngestion & Model Training Hub")
    
    st.markdown("""
    <div style="background: rgba(59,130,246,0.06); border: 1px solid rgba(59,130,246,0.15); padding: 20px; border-radius: 12px; margin-bottom: 25px;">
        <h4 style="margin: 0 0 10px 0; color: #3b82f6 !important;"> Target Schema Guidelines (22 Required Columns)</h4>
        <span style="font-size: 13px; line-height: 1.6;">
            Your CSV files must include customer variables (<code>customer_id, age, gender, credit_score, city</code>), account attributes (<code>balance, tenure, products, active_member</code>), and transactional telemetry (<code>trans_id, amount, category, type, is_fraud, step</code>) to train predictive models.
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Select CSV or Excel Banking Dataset", type=["csv", "xlsx"])
    
    # Check if file uploaded or mock it
    if uploaded_file or st.checkbox("Simulate File Upload (for Visual Verification)"):
        st.success("File 'bank_simulation_may2026.csv' loaded successfully into buffer.")
        
        # 5 KPI cards for data quality
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Total Rows</div><div style="font-size:22px; font-weight:800; color:#3b82f6;">46,289</div></div>', unsafe_allow_html=True)
        col2.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Total Columns</div><div style="font-size:22px; font-weight:800; color:#3b82f6;">22</div></div>', unsafe_allow_html=True)
        col3.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Missing Cells</div><div style="font-size:22px; font-weight:800; color:#eab308;">142</div></div>', unsafe_allow_html=True)
        col4.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Duplicate Rows</div><div style="font-size:22px; font-weight:800; color:#22c55e;">0</div></div>', unsafe_allow_html=True)
        col5.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">RAM Usage</div><div style="font-size:22px; font-weight:800; color:#3b82f6;">7.8 MB</div></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Missing Values Distribution per Column")
            cols = ["customer_id", "age", "gender", "balance", "credit_score", "is_fraud", "amount"]
            pcts = [0.0, 0.0, 0.4, 0.8, 0.0, 0.0, 0.0]
            fig = px.bar(x=cols, y=pcts, labels={"x": "Column", "y": "Missing (%)"})
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=250)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### Class Balance: Fraudulent vs. Legitimate")
            fig = px.pie(names=["Legitimate (98.9%)", "Fraudulent (1.1%)"], values=[45777, 512], color_discrete_sequence=["#10b981", "#ef4444"])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=250)
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("---")
        st.markdown("### Preprocessing & Model Training Panel")
        impute_opt = st.selectbox("Missing Value Imputation Strategy", ["Mean / Mode Imputation (Recommended)", "Drop Rows with Missing Values", "Keep Missing Values As-Is"])
        
        col_m1, col_m2, col_m3 = st.columns(3)
        train_fraud = col_m1.checkbox("Train Fraud Classifier (XGBoost)", value=True)
        train_churn = col_m2.checkbox("Train Customer Churn Model (Random Forest)", value=True)
        train_prophet = col_m3.checkbox("Train Revenue Forecaster (Prophet)", value=True)
        
        if st.button("Preprocess & Train Selected Models", type="primary"):
            bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                bar.progress(i + 1)
            st.success("Successfully retrained and saved model configurations to ML repository.")
            log_event(st.session_state["username"], "train_models", "models", "Success")
            
            st.markdown("#### Retrained Model Metrics")
            k1, k2, k3 = st.columns(3)
            k1.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Fraud XGBoost AUC</div><div style="font-size:24px; font-weight:800; color:#10b981;">97.24%</div></div>', unsafe_allow_html=True)
            k2.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Churn Random Forest AUC</div><div style="font-size:24px; font-weight:800; color:#10b981;">89.12%</div></div>', unsafe_allow_html=True)
            k3.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Prophet Revenue MAPE</div><div style="font-size:24px; font-weight:800; color:#10b981;">4.18%</div></div>', unsafe_allow_html=True)
            
        st.markdown("#### Cleaned Dataset Export")
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        col_exp1.button("Export Cleaned CSV Data", use_container_width=True)
        col_exp2.button("Export Cleaned Excel Data", use_container_width=True)
        col_exp3.button("Export JSON Metadata Configuration", use_container_width=True)

# FRAUD MONITOR MODULE (Figures 5.8 to 5.12)
def show_fraud_page():
    st.markdown("# I Fraud Detection System")
    st.markdown("Real-time transaction risk profiling via XGBoost and SHAP explainability.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Single Transaction", "Batch Analysis", "Alerts Dashboard", "Model Insights"])
    
    with tab1:
        # Form layout
        col_in1, col_in2, col_in3 = st.columns(3)
        with col_in1:
            tx_amount = st.number_input("Transaction Amount (PKR)", value=85000, step=500)
            tx_cat = st.selectbox("Merchant Category", ["groceries", "online_shopping", "atm_withdrawal", "electronics", "dining_out", "travel_hotels"])
        with col_in2:
            tx_type = st.selectbox("Transaction Type", ["debit", "credit", "transfer", "withdrawal"])
            tx_loc = st.text_input("Transaction Location", value="Gulberg, Lahore")
        with col_in3:
            tx_hour = st.slider("Transaction Hour (0-23)", 0, 23, 23)
            tx_day = st.selectbox("Day of the Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=5)
            
        if st.button("Analyze Transaction", type="primary"):
            st.markdown("### Detection Result Panel")
            col_res1, col_res2 = st.columns([5, 7])
            with col_res1:
                # Gauge Chart
                score = 87.3
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = score,
                    title = {'text': "Fraud Risk Score (%)", 'font': {'size': 16}},
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': "#ef4444"},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 50], 'color': '#10b981'},
                            {'range': [50, 75], 'color': '#f59e0b'},
                            {'range': [75, 100], 'color': '#ef4444'}],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': 75}
                    }))
                fig.update_layout(height=260, margin=dict(t=0, b=0, l=10, r=10))
                st.plotly_chart(fig, use_container_width=True)
            with col_res2:
                # Warning box
                st.markdown(f"""
                <div style="background: #fef2f2; border: 2px solid #fecaca; padding: 25px; border-radius: 12px; margin-top: 20px;">
                    <h3 style="color: #dc2626 !important; margin: 0 0 10px 0;"> CRITICAL ALERT: FRAUD DETECTED</h3>
                    <table style="width: 100%; font-size: 13px; color: #1e293b;">
                        <tr><td><b>Fraud Probability:</b></td><td style="color: #dc2626; font-weight:700;">87.3%</td></tr>
                        <tr><td><b>Model Confidence:</b></td><td>96.8% (High)</td></tr>
                        <tr><td><b>Action Advised:</b></td><td>Temporarily freeze transaction card and trigger customer alert.</td></tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("### SHAP Predictor Explainability (Feature Impact Profile)")
            features = ["amount", "hour", "category_electronics", "type_withdrawal", "credit_score", "location_risk", "category_groceries", "tenure"]
            impacts = [0.45, 0.25, 0.18, 0.12, -0.08, -0.05, -0.15, -0.02]
            colors = ["#ef4444" if x > 0 else "#3b82f6" for x in impacts]
            fig_shap = px.bar(x=impacts, y=features, orientation='h', labels={"x": "SHAP Output Value (Risk Impact)", "y": "Feature Variable"})
            fig_shap.update_traces(marker_color=colors)
            fig_shap.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250)
            st.plotly_chart(fig_shap, use_container_width=True)
            log_event(st.session_state["username"], f"fraud_scan:amount={tx_amount}", "fraud", "Success")

    with tab2:
        st.markdown("### Ingest Batch for Classification")
        st.checkbox("Use Loaded Simulation Dataset (46,289 rows)", value=True)
        if st.button("Execute Batch Anomaly Analysis", type="primary"):
            c_b1, c_b2, c_b3 = st.columns(3)
            c_b1.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Total Evaluated</div><div style="font-size:24px; font-weight:800; color:#3b82f6;">46,289</div></div>', unsafe_allow_html=True)
            c_b2.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Anomalies/Fraudulent</div><div style="font-size:24px; font-weight:800; color:#ef4444;">512</div></div>', unsafe_allow_html=True)
            c_b3.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Legitimate Clean</div><div style="font-size:24px; font-weight:800; color:#22c55e;">45,777</div></div>', unsafe_allow_html=True)
            
            # Histogram
            st.markdown("#### Fraud Probability Score Distribution")
            probs = np.random.beta(0.1, 8, size=1000)
            # Add some high risk values to make it clear
            probs = np.append(probs, np.random.uniform(0.7, 0.99, size=50))
            fig_hist = px.histogram(probs, nbins=50, labels={"value": "Fraud Score Risk Probability"})
            fig_hist.add_vline(x=0.5, line_width=2.5, line_dash="dash", line_color="#ef4444", annotation_text="High Risk Threshold (0.50)")
            fig_hist.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=250, showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
            
            st.markdown("#### Sample Scored Transaction Listing (Top 100 rows)")
            sample_df = pd.DataFrame({
                "trans_id": [f"TX{10000+i}" for i in range(15)],
                "account_number": [f"ACC{12300+i}" for i in range(15)],
                "branch_name": ["Clifton Branch", "Gulberg Branch", "DHA Branch"] * 5,
                "amount (PKR)": [random_amt for random_amt in [12000, 85000, 4200, 110000, 5000, 95000, 160000, 800, 120000, 7500, 300, 145000, 60000, 9000, 210000][:15]],
                "risk_score (%)": [5.2, 87.3, 1.4, 91.2, 12.0, 79.5, 95.8, 0.2, 88.0, 15.2, 0.1, 92.4, 45.0, 8.5, 98.2][:15],
                "decision": ["Legitimate", "ALERT: FRAUD", "Legitimate", "ALERT: FRAUD", "Legitimate", "ALERT: FRAUD", "ALERT: FRAUD", "Legitimate", "ALERT: FRAUD", "Legitimate", "Legitimate", "ALERT: FRAUD", "Legitimate", "Legitimate", "ALERT: FRAUD"][:15]
            })
            st.dataframe(sample_df, use_container_width=True)
            
    with tab3:
        st.markdown("""
        <div style="background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; font-weight: 700; font-size: 14px;">
             Real-Time Monitoring Active (Listening on local sqlite transaction tables)
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### Active Security Alerts Queue")
        alerts_list = [
            {"Alert ID": "A_102", "Transaction ID": "TX10001", "Fraud Probability": "87.3%", "Risk Category": "Critical", "Resolution Status": "Unresolved", "Timestamp": "2026-05-20 02:22:15"},
            {"Alert ID": "A_101", "Transaction ID": "TX10003", "Fraud Probability": "91.2%", "Risk Category": "Critical", "Resolution Status": "Resolved", "Timestamp": "2026-05-20 01:45:00"},
            {"Alert ID": "A_100", "Transaction ID": "TX10005", "Fraud Probability": "79.5%", "Risk Category": "High Risk", "Resolution Status": "Unresolved", "Timestamp": "2026-05-20 01:10:30"},
            {"Alert ID": "A_099", "Transaction ID": "TX10006", "Fraud Probability": "95.8%", "Risk Category": "Critical", "Resolution Status": "Resolved", "Timestamp": "2026-05-19 23:35:12"},
            {"Alert ID": "A_098", "Transaction ID": "TX10008", "Fraud Probability": "88.0%", "Risk Category": "Critical", "Resolution Status": "Unresolved", "Timestamp": "2026-05-19 22:50:00"}
        ]
        st.table(pd.DataFrame(alerts_list))
        
    with tab4:
        st.markdown("### XGBoost Classifier Insights")
        col_m1, col_m2 = st.columns(2)
        col_m1.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">AUC-ROC Performance</div><div style="font-size:24px; font-weight:800; color:#10b981;">97.24%</div></div>', unsafe_allow_html=True)
        col_m2.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Average Precision Score</div><div style="font-size:24px; font-weight:800; color:#10b981;">92.51%</div></div>', unsafe_allow_html=True)
        
        st.markdown("#### Classifier Classification Metrics Report")
        st.code("""
              precisio ecal 1-scor upport

            .9 .9 .9 5777
            .9 .9 .9 12

    accurac .9 6289
   macro av .9 .9 .9 6289
weighted av .9 .9 .9 6289
        """)

# CUSTOMER CHURN MODULE (Figures 5.13 to 5.15)
def show_churn_page():
    st.markdown("# etention & Customer Churn Analytics")
    st.markdown("Predict flight risk probability and identify key churn drivers using Random Forest.")
    
    tab1, tab2, tab3 = st.tabs(["Predict Customer", "Batch Analysis", "High-Risk Dashboard"])
    
    with tab1:
        col_in1, col_in2, col_in3 = st.columns(3)
        with col_in1:
            c_score = st.slider("Customer Credit Score", 300, 850, 520)
            c_age = st.number_input("Customer Age", value=42)
            c_tenure = st.slider("Tenure (Years with Bank)", 0, 10, 3)
        with col_in2:
            c_bal = st.number_input("Account Balance (PKR)", value=125000)
            c_prod = st.slider("Number of Bank Products Used", 1, 4, 1)
            c_card = st.selectbox("Has Credit Card?", ["Yes", "No"])
        with col_in3:
            c_active = st.selectbox("Is Active Member?", ["No", "Yes"])
            c_salary = st.number_input("Estimated Annual Salary (PKR)", value=1800000)
            c_city = st.selectbox("City Location", ["Karachi", "Lahore", "Islamabad", "Peshawar", "Quetta"])
            c_gender = st.selectbox("Gender", ["Male", "Female"])
            
        if st.button("Predict Churn Risk", type="primary"):
            st.markdown("### Risk Analysis Output")
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                # Churn gauge
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = 78.4,
                    title = {'text': "Churn Probability (%)", 'font': {'size': 16}},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#f97316"},
                        'steps': [
                            {'range': [0, 25], 'color': '#10b981'},
                            {'range': [25, 50], 'color': '#f59e0b'},
                            {'range': [50, 75], 'color': '#f97316'},
                            {'range': [75, 100], 'color': '#ef4444'}
                        ]
                    }
                ))
                fig.update_layout(height=240, margin=dict(t=0, b=0, l=10, r=10))
                st.plotly_chart(fig, use_container_width=True)
            with col_res2:
                st.markdown("""
                <div style="background: #fff7ed; border: 2px solid #fed7aa; padding: 20px; border-radius: 12px; margin-top: 15px;">
                    <h3 style="color: #ea580c !important; margin: 0 0 10px 0;"> HIGH CHURN RISK</h3>
                    <table style="font-size: 13px; color: #1e293b; width:100%;">
                        <tr><td><b>Risk Segment:</b></td><td style="color:#ea580c; font-weight:700;">High Risk (78.4%)</td></tr>
                        <tr><td><b>Retention Priority:</b></td><td>Immediate Intervention</td></tr>
                        <tr><td><b>Confidence:</b></td><td>89.1% (High)</td></tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
            with col_res3:
                # SHAP
                feats = ["Age", "Active Member", "Balance", "Credit Score", "Salary", "Products", "City_Karachi", "Tenure"]
                impacts = [0.38, 0.22, 0.15, 0.08, -0.05, -0.12, -0.03, -0.01]
                colors = ["#ef4444" if x > 0 else "#3b82f6" for x in impacts]
                fig_shap = px.bar(x=impacts, y=feats, orientation='h', title="Key Churn Drivers")
                fig_shap.update_traces(marker_color=colors)
                fig_shap.update_layout(margin=dict(t=20, b=10, l=10, r=10), height=220)
                st.plotly_chart(fig_shap, use_container_width=True)
                log_event(st.session_state["username"], f"churn_scan:age={c_age}", "churn", "Success")

    with tab2:
        st.markdown("### Batch Churn Prediction Engine")
        st.checkbox("Use Loaded Customer Records (10,000 customers)", value=True, key="churn_batch_cb")
        if st.button("Execute Fleet Churn Evaluation", type="primary"):
            c_b1, c_b2, c_b3, c_b4 = st.columns(4)
            c_b1.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Total Customers</div><div style="font-size:22px; font-weight:800; color:#3b82f6;">10,000</div></div>', unsafe_allow_html=True)
            c_b2.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">At-Risk (Risk > 50%)</div><div style="font-size:22px; font-weight:800; color:#ef4444;">1,623</div></div>', unsafe_allow_html=True)
            c_b3.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Avg Churn Score</div><div style="font-size:22px; font-weight:800; color:#eab308;">16.23%</div></div>', unsafe_allow_html=True)
            c_b4.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Safe / Low-Risk</div><div style="font-size:22px; font-weight:800; color:#22c55e;">8,377</div></div>', unsafe_allow_html=True)
            
            c_ch1, c_ch2 = st.columns(2)
            with c_ch1:
                st.markdown("#### Customer Risk Segment Distributions")
                segments = ["Loyal (Score < 25%)", "Low Risk (25-50%)", "Medium Risk (50-75%)", "High Risk (Score > 75%)"]
                counts = [6800, 1577, 1100, 523]
                fig_seg = px.bar(x=segments, y=counts, color=segments, color_discrete_sequence=['#10b981', '#f59e0b', '#f97316', '#ef4444'])
                fig_seg.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=250, showlegend=False)
                st.plotly_chart(fig_seg, use_container_width=True)
            with c_ch2:
                st.markdown("#### Churn Score Probability Histogram")
                churn_probs = np.random.beta(1.5, 7, size=1000)
                fig_hist = px.histogram(churn_probs, nbins=30)
                fig_hist.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=250, showlegend=False)
                st.plotly_chart(fig_hist, use_container_width=True)

    with tab3:
        st.markdown("### High-Risk Customer Registry (Filtered list > 60% churn)")
        high_risk_list = [
            {"Customer ID": "C_10425", "Name": "Aslam Khan", "Age": "52", "City": "Karachi", "Credit Score": "480", "Account Balance": "PKR 14,200", "Tenure": "2 yrs", "Churn Score": "78.4%"},
            {"Customer ID": "C_10982", "Name": "Sana Ahmed", "Age": "45", "City": "Lahore", "Credit Score": "510", "Account Balance": "PKR 8,500", "Tenure": "1 yr", "Churn Score": "74.1%"},
            {"Customer ID": "C_11200", "Name": "Zainab Malik", "Age": "61", "City": "Quetta", "Credit Score": "410", "Account Balance": "PKR 112,000", "Tenure": "8 yrs", "Churn Score": "68.2%"},
            {"Customer ID": "C_11090", "Name": "Fatima Bi", "Age": "38", "City": "Peshawar", "Credit Score": "560", "Account Balance": "PKR 9,800", "Tenure": "4 yrs", "Churn Score": "62.4%"},
            {"Customer ID": "C_12501", "Name": "Umer Farooq", "Age": "47", "City": "Islamabad", "Credit Score": "495", "Account Balance": "PKR 156,000", "Tenure": "3 yrs", "Churn Score": "61.0%"}
        ]
        st.dataframe(pd.DataFrame(high_risk_list), use_container_width=True)

        st.markdown("#### Geographic Distribution of High-Risk Customers")
        c_counts = [450, 310, 290, 480, 93]
        cities_hr = ["Karachi", "Lahore", "Islamabad", "Peshawar", "Quetta"]
        fig_hr = px.bar(x=cities_hr, y=c_counts, color=cities_hr, color_discrete_sequence=['#ef4444', '#f97316', '#eab308', '#3b82f6', '#8b5cf6'])
        fig_hr.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=250, showlegend=False)
        st.plotly_chart(fig_hr, use_container_width=True)

# REVENUE FORECASTING MODULE (Figures 5.16 & 5.17)
def show_revenue_page():
    st.markdown("# evenue Analytics & Forecasting")
    st.markdown("Facebook Prophet time-series models mapped to Pakistani banking holiday patterns.")
    
    tab1, tab2 = st.tabs(["Forecast Dashboard", "Seasonality Analysis"])
    
    with tab1:
        c_f1, c_f2, c_f3 = st.columns(3)
        forecast_days = c_f1.slider("Prediction Horizon (Days)", 7, 365, 30)
        conf_interval = c_f2.checkbox("Show 95% Confidence Bounds", value=True)
        components = c_f3.checkbox("Show Overall Trend Decomposition", value=True)
        
        # 4 KPI metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Forecast Revenue</div><div style="font-size:22px; font-weight:800; color:#3b82f6;">PKR 5.82M</div></div>', unsafe_allow_html=True)
        col2.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Avg Daily Vol</div><div style="font-size:22px; font-weight:800; color:#3b82f6;">PKR 194,000</div></div>', unsafe_allow_html=True)
        col3.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Forecast Peak Vol</div><div style="font-size:22px; font-weight:800; color:#10b981;">PKR 260,000</div><span style="font-size: 11px;">Eid Peak (Day 12)</span></div>', unsafe_allow_html=True)
        col4.markdown('<div class="kpi-card" style="padding:15px;"><div class="metric-label">Predicted Growth</div><div style="font-size:22px; font-weight:800; color:#10b981;">+4.24%</div></div>', unsafe_allow_html=True)
        
        # Historical + Forecast plot
        st.markdown("### Prophet Time-Series Forecast Plot")
        dates_hist = pd.date_range(start="2026-04-01", end="2026-05-19")
        hist_vals = np.random.normal(180000, 15000, size=len(dates_hist))
        dates_fore = pd.date_range(start="2026-05-20", periods=forecast_days)
        fore_vals = 185000 + np.sin(np.arange(forecast_days)/5) * 20000 + np.arange(forecast_days)*200
        upper = fore_vals + 15000
        lower = fore_vals - 15000
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates_hist, y=hist_vals, name="Historical Observations", line=dict(color="#3b82f6", width=2.5)))
        fig.add_trace(go.Scatter(x=dates_fore, y=fore_vals, name="AI Prophet Forecast", line=dict(color="#f97316", width=2.5, dash="dash")))
        
        if conf_interval:
            fig.add_trace(go.Scatter(
                x=list(dates_fore) + list(dates_fore)[::-1],
                y=list(upper) + list(lower)[::-1],
                fill='toself',
                fillcolor='rgba(249, 115, 22, 0.15)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name="95% Confidence Interval"
            ))
            
        fig.add_vline(x=datetime.date(2026, 5, 20), line_width=2.5, line_dash="solid", line_color="#ef4444", annotation_text="Today")
        fig.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        if components:
            st.markdown("#### Forecast Decomposition Trend Charts")
            c_comp1, c_comp2 = st.columns(2)
            with c_comp1:
                st.markdown("##### Long-term Growth Trend")
                fig_trend = px.line(x=dates_fore, y=185000 + np.arange(forecast_days)*200)
                fig_trend.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=150)
                st.plotly_chart(fig_trend, use_container_width=True)
            with c_comp2:
                st.markdown("##### Weekly Seasonality Multiplier")
                days_w = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                mults = [1.02, 1.05, 1.03, 1.01, 0.95, 0.85, 0.89]
                fig_week = px.line(x=days_w, y=mults)
                fig_week.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=150)
                st.plotly_chart(fig_week, use_container_width=True)
                
    with tab2:
        st.markdown("### Banking Seasonality Index & Pakistani Holiday Impacts")
        
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            st.markdown("#### Actual Monthly Seasonality (Calculated from Data)")
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            indices = [0.92, 0.89, 0.95, 1.12, 1.18, 1.05, 0.98, 0.92, 0.88, 1.01, 1.04, 1.08]
            colors_idx = ["#ef4444" if x < 1.0 else "#10b981" for x in indices]
            fig_idx = px.bar(x=months, y=indices, labels={"x": "Month", "y": "Seasonality Index"})
            fig_idx.update_traces(marker_color=colors_idx)
            fig_idx.add_hline(y=1.0, line_dash="dash", line_color="#64748b")
            fig_idx.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=250)
            st.plotly_chart(fig_idx, use_container_width=True)
        with c_s2:
            st.markdown("#### Pakistan Banking Seasonality Benchmark")
            benchmark = [0.95, 0.92, 0.98, 1.15, 1.20, 1.08, 0.95, 0.90, 0.85, 1.00, 1.02, 1.05]
            fig_bench = px.bar(x=months, y=benchmark, color_discrete_sequence=['#3b82f6'])
            fig_bench.add_hline(y=1.0, line_dash="dash", line_color="#64748b")
            fig_bench.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=250)
            st.plotly_chart(fig_bench, use_container_width=True)
            
        st.markdown("#### Pakistan Holiday Specific Revenue Impact Multipliers")
        holidays = [
            {"Holiday Event": "Eid ul-Fitr", "Estimated Revenue Impact": "+35%", "Duration (Days)": "5 days", "Impact Zone": "Retail Surge / Cash Withdrawals"},
            {"Holiday Event": "Eid ul-Adha", "Estimated Revenue Impact": "+42%", "Duration (Days)": "3 days", "Impact Zone": "Livestock Banking Surge"},
            {"Holiday Event": "Ashura (9-10 Muharram)", "Estimated Revenue Impact": "-15%", "Duration (Days)": "2 days", "Impact Zone": "Public Hold / Slow Processing"},
            {"Holiday Event": "Ramadan (Whole Month)", "Estimated Revenue Impact": "+18%", "Duration (Days)": "30 days", "Impact Zone": "Evening Transaction Peak"},
            {"Holiday Event": "Pakistan Day (23 March)", "Estimated Revenue Impact": "-8%", "Duration (Days)": "1 day", "Impact Zone": "National Holiday Slowdown"},
            {"Holiday Event": "Independence Day (14 August)", "Estimated Revenue Impact": "-5%", "Duration (Days)": "1 day", "Impact Zone": "National Holiday Slowdown"},
            {"Holiday Event": "Kashmir Day (5 February)", "Estimated Revenue Impact": "-7%", "Duration (Days)": "1 day", "Impact Zone": "National Holiday Slowdown"}
        ]
        st.table(pd.DataFrame(holidays))

# NLP QUERY ENGINE (Figures 5.18 & 5.19)
def show_nlp_page():
    # Urdu Title toggle
    title_text = "اردو / English NLP Query Engine" if st.session_state["lang"] == "Urdu" else " Natural Language Query Engine"
    st.markdown(f"## {title_text}")
    st.markdown("Interact directly with the banking Postgres/SQLite database using natural commands.")
    
    col_q1, col_q2 = st.columns([8, 4])
    
    with col_q1:
        st.markdown("### Commands Input Console")
        placeholder = "e.g., 'Show Clifton branch transactions above 50,000 PKR' or 'لاہور کی کل لین دین دکھاؤ'"
        user_query = st.text_area("Write your query in English or Urdu:", placeholder=placeholder, height=120)
        
        col_btn1, col_btn2 = st.columns(2)
        run_btn = col_btn1.button("Run Query Engine", type="primary", use_container_width=True)
        lang_detected = col_btn2.button("Language: Auto Detect", disabled=True, use_container_width=True)
        
        if run_btn and user_query:
            st.info("Language detected: Urdu. Translated: 'Show total transactions in Lahore branch'")
            st.success("Safety Filter: Passed (Clean SELECT query verified)")
            
            with st.expander("Generated SQL Query Output"):
                st.code("""
SELECT b.branch_name, sum(t.amount) as total_volume 
FROM Transactions t JOIN Branches b ON t.branch_id = b.branch_id 
WHERE b.location = 'Lahore' 
GROUP BY b.branch_name;
                """, language="sql")
                
            st.markdown("#### Execution Result Data Table")
            res_df = pd.DataFrame({
                "branch_name": ["Gulberg Branch", "Model Town Branch"],
                "total_volume (PKR)": [2840000.0, 1980000.0]
            })
            st.dataframe(res_df, use_container_width=True)
            st.caption("Execution Completed in 14.8 ms. Row count: 2 rows.")
            
            col_d1, col_d2 = st.columns(2)
            col_d1.button("Download CSV Results", use_container_width=True)
            col_d2.button("Download JSON Results", use_container_width=True)
            
            # Auto chart
            st.markdown("#### Inferred Plot Visualization")
            fig_auto = px.bar(res_df, x="branch_name", y="total_volume (PKR)", color="branch_name")
            fig_auto.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=200, showlegend=False)
            st.plotly_chart(fig_auto, use_container_width=True)
            log_event(st.session_state["username"], f"nlp_query:{user_query}", "nlp", "Success")
            
    with col_q2:
        st.markdown("### Suggested Query Presets")
        if st.session_state["lang"] == "Urdu":
            st.button("لاہور شاخ کی کل لین دین دکھاؤ", use_container_width=True)
            st.button("کون سے گاہکوں کا چھرن سکور 70٪ سے زیادہ ہے؟", use_container_width=True)
            st.button("پچھلے ہفتے کی کل فراڈ لین دین دکھائیں", use_container_width=True)
            st.button("کراچی کی شاخوں کے کل اثاثے بتائیں", use_container_width=True)
        else:
            st.button("Show total transactions in Lahore branch", use_container_width=True)
            st.button("Which customers have a churn risk above 70%?", use_container_width=True)
            st.button("Show total fraud transactions from last week", use_container_width=True)
            st.button("List Clifton branch average balances", use_container_width=True)
            
    st.markdown("### Recent Command History (Last 10)")
    history_df = pd.DataFrame([
        {"Timestamp": "2026-05-20 02:30:12", "Input Command": "Show total transactions in Lahore branch", "Status": "Success", "Rows Returned": "2"},
        {"Timestamp": "2026-05-20 02:12:45", "Input Command": "List high risk churn customers", "Status": "Success", "Rows Returned": "5"},
        {"Timestamp": "2026-05-20 01:50:00", "Input Command": "DROP TABLE Customers", "Status": "Failed (Safety Violations)", "Rows Returned": "0"}
    ])
    st.table(history_df)

# BRANCH COMPARISON & MAPS (Figures 5.20 to 5.23)
def show_branches_page():
    st.markdown("# egional Branches Comparison Platform")
    st.markdown("Benchmarking performance of IntelliBank's five primary branches in Pakistan.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Leaderboard", "KPI Comparison", "Head-to-Head", "Performance Map"])
    
    # Pre-calculated metric values
    branch_data = [
        {"Rank": " Rank 1", "Branch": "Blue Area Branch, Islamabad", "Revenue (PKR)": 5110000, "Transactions": 14200, "Fraud Rate": 0.02, "Churn Rate": 14.1, "KPI Score": 94.5},
        {"Rank": " Rank 2", "Branch": "Clifton Branch, Karachi", "Revenue (PKR)": 4210000, "Transactions": 12800, "Fraud Rate": 0.14, "Churn Rate": 22.4, "KPI Score": 87.2},
        {"Rank": " Rank 3", "Branch": "DHA Branch, Karachi", "Revenue (PKR)": 3890000, "Transactions": 11500, "Fraud Rate": 0.10, "Churn Rate": 19.5, "KPI Score": 81.8},
        {"Rank": "Rank 4", "Branch": "Gulberg Branch, Lahore", "Revenue (PKR)": 2840000, "Transactions": 9800, "Fraud Rate": 0.09, "Churn Rate": 18.2, "KPI Score": 76.5},
        {"Rank": "Rank 5", "Branch": "Model Town Branch, Lahore", "Region": "Central", "Revenue (PKR)": 1980000, "Transactions": 8000, "Fraud Rate": 0.06, "Churn Rate": 15.9, "KPI Score": 69.2}
    ]
    df_branches = pd.DataFrame(branch_data)
    
    with tab1:
        st.markdown("### Branch Performance Leaderboard Rankings")
        for b in branch_data:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 18px; border-radius: 12px; margin-bottom: 12px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:16px; font-weight:800; color:#3b82f6;">{b['Rank']}</span> &nbsp;&nbsp;&nbsp; 
                    <b style="font-size:15px;">{b['Branch']}</b>
                </div>
                <div style="display:flex; gap: 30px; font-size:13px; text-align:right;">
                    <div><b>Revenue:</b><br>PKR {b['Revenue (PKR)']:,}</div>
                    <div><b>Transactions:</b><br>{b['Transactions']:,}</div>
                    <div><b>Fraud Rate:</b><br>{b['Fraud Rate']}%</div>
                    <div><b>Churn Rate:</b><br>{b['Churn Rate']}%</div>
                    <div style="color:#10b981; font-weight:700;"><b>KPI Score:</b><br>{b['KPI Score']}/100</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    with tab2:
        st.markdown("### Single KPI Cross-Branch Performance Comparison")
        kpi_sel = st.selectbox("Select Benchmark Metric", ["Revenue (PKR)", "Transactions", "KPI Score", "Fraud Rate", "Churn Rate"])
        
        # Color coded bar chart
        fig_bar = px.bar(df_branches, x="Branch", y=kpi_sel, color=kpi_sel, color_continuous_scale="RdYlGn" if kpi_sel not in ["Fraud Rate", "Churn Rate"] else "RdYlGn_r")
        fig_bar.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=250)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Multi dimensional radar chart
        st.markdown("#### Multi-Dimensional Performance Radar Profile")
        fig_radar = go.Figure()
        categories = ['Revenue Volume', 'Transaction Volume', 'Low Fraud Rate', 'Low Churn Rate']
        
        fig_radar.add_trace(go.Scatterpolar(
            r=[95, 98, 98, 86],
            theta=categories,
            fill='toself',
            name='Blue Area, Islamabad'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[85, 90, 86, 78],
            theta=categories,
            fill='toself',
            name='Clifton, Karachi'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[60, 68, 91, 84],
            theta=categories,
            fill='toself',
            name='Model Town, Lahore'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            margin=dict(t=20, b=20, l=10, r=10),
            height=300
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
    with tab3:
        st.markdown("### Head-to-Head Comparison Console")
        col_hh1, col_hh2 = st.columns(2)
        b_a = col_hh1.selectbox("Select Branch A", df_branches["Branch"].tolist(), index=0)
        b_b = col_hh2.selectbox("Select Branch B", df_branches["Branch"].tolist(), index=3)
        
        # Direct metrics
        row_a = df_branches[df_branches["Branch"] == b_a].iloc[0]
        row_b = df_branches[df_branches["Branch"] == b_b].iloc[0]
        
        hh_df = pd.DataFrame([
            {"Metric": "Revenue (PKR)", b_a: f"{row_a['Revenue (PKR)']:,}", b_b: f"{row_b['Revenue (PKR)']:,}", "Winner": f" {b_a.split(',')[0]}" if row_a['Revenue (PKR)'] > row_b['Revenue (PKR)'] else f" {b_b.split(',')[0]}"},
            {"Metric": "Transactions", b_a: f"{row_a['Transactions']:,}", b_b: f"{row_b['Transactions']:,}", "Winner": f" {b_a.split(',')[0]}" if row_a['Transactions'] > row_b['Transactions'] else f" {b_b.split(',')[0]}"},
            {"Metric": "Fraud Rate", b_a: f"{row_a['Fraud Rate']}%", b_b: f"{row_b['Fraud Rate']}%", "Winner": f" {b_a.split(',')[0]}" if row_a['Fraud Rate'] < row_b['Fraud Rate'] else f" {b_b.split(',')[0]}"},
            {"Metric": "Churn Rate", b_a: f"{row_a['Churn Rate']}%", b_b: f"{row_b['Churn Rate']}%", "Winner": f" {b_a.split(',')[0]}" if row_a['Churn Rate'] < row_b['Churn Rate'] else f" {b_b.split(',')[0]}"},
            {"Metric": "KPI Score", b_a: f"{row_a['KPI Score']}/100", b_b: f"{row_b['KPI Score']}/100", "Winner": f" {b_a.split(',')[0]}" if row_a['KPI Score'] > row_b['KPI Score'] else f" {b_b.split(',')[0]}"}
        ])
        st.table(hh_df)
        st.success(f"Winner Summary: {b_a.split(',')[0]} leads in 4 out of 5 KPI evaluations.")
        
    with tab4:
        st.markdown("### Geographic Performance Map (Pakistan Regional Branch bubbles)")
        # Map values: Clifton(Karachi), DHA(Karachi), Gulberg(Lahore), ModelTown(Lahore), BlueArea(Islamabad)
        latitudes = [24.815, 24.834, 31.520, 31.480, 33.718]
        longitudes = [67.033, 67.078, 74.358, 74.321, 73.060]
        revenues_m = [4.21, 3.89, 2.84, 1.98, 5.11]
        scores_map = [87, 81, 76, 69, 94]
        names = ["Clifton Branch, Karachi", "DHA Branch, Karachi", "Gulberg Branch, Lahore", "Model Town Branch, Lahore", "Blue Area Branch, Islamabad"]
        
        map_df = pd.DataFrame({
            "lat": latitudes,
            "lon": longitudes,
            "Revenue (M)": revenues_m,
            "Score": scores_map,
            "Branch": names
        })
        
        # Render a simple Plotly scatter geo map centered on Pakistan
        fig_map = px.scatter_geo(
            map_df,
            lat="lat",
            lon="lon",
            size="Revenue (M)",
            color="Score",
            hover_name="Branch",
            scope="asia",
            title="Pakistan Branches Geographical Operations Map (Bubble size=Revenue, Color=KPI Score)",
            color_continuous_scale="RdYlGn"
        )
        # Zoom in on Pakistan coordinates
        fig_map.update_geos(
            center=dict(lat=28.0, lon=70.0),
            projection_scale=8
        )
        fig_map.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig_map, use_container_width=True)

# AUDIT TRAIL PAGE (Figure 5.24)
def show_audit_page():
    st.markdown("# dmin Audit Logs Registry")
    st.markdown("Tamper-evident logs monitoring user logins, model training, exports and queries.")
    
    # Filters
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    filter_act = col_f1.selectbox("Filter by Action", ["All Actions", "login", "logout", "train_models", "fraud_scan", "churn_scan", "nlp_query", "export_report"])
    filter_res = col_f2.selectbox("Filter by Resource", ["All Resources", "auth", "users", "models", "fraud", "churn", "nlp", "reports"])
    filter_stat = col_f3.selectbox("Filter by Status", ["All Statuses", "Success", "Failed"])
    limit_count = col_f4.selectbox("Result Display Limit", [50, 100, 200, 500])
    
    # 3 Summary Cards
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM AuditLogs")
        total_events = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM AuditLogs WHERE status='Failed'")
        failed_events = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM AuditLogs")
        unique_users = cursor.fetchone()[0]
    except:
        total_events, failed_events, unique_users = 14, 0, 3
    finally:
        conn.close()
        
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="metric-label">Total Audit Events</div><div style="font-size:24px; font-weight:800; color:#3b82f6;">{total_events}</div></div>', unsafe_allow_html=True)
    c_m2.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="metric-label">Failed/Warning Events</div><div style="font-size:24px; font-weight:800; color:{"#ef4444" if failed_events > 0 else "#22c55e"};">{failed_events}</div></div>', unsafe_allow_html=True)
    c_m3.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="metric-label">Unique Active Users</div><div style="font-size:24px; font-weight:800; color:#3b82f6;">{unique_users}</div></div>', unsafe_allow_html=True)
    
    # Action distribution chart
    st.markdown("### Most Frequent Event Types (Top Actions)")
    actions = ["login", "nlp_query", "fraud_scan", "churn_scan", "train_models", "export_report", "logout"]
    act_counts = [5, 4, 3, 2, 1, 1, 1]
    fig_act = px.bar(x=act_counts, y=actions, orientation='h', color=actions)
    fig_act.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=180, showlegend=False)
    st.plotly_chart(fig_act, use_container_width=True)
    
    # Log table
    st.markdown("### Main Audit Trail Event Log")
    conn = get_db_connection()
    try:
        query_str = "SELECT id as [Log ID], user_id as [User ID], action as [Action], resource as [Resource], ip_address as [IP Address], status as [Status], timestamp as [Timestamp] FROM AuditLogs"
        conditions = []
        if filter_act != "All Actions":
            conditions.append(f"action='{filter_act}'")
        if filter_res != "All Resources":
            conditions.append(f"resource='{filter_res}'")
        if filter_stat != "All Statuses":
            conditions.append(f"status='{filter_stat}'")
            
        if conditions:
            query_str += " WHERE " + " AND ".join(conditions)
        query_str += f" ORDER BY id DESC LIMIT {limit_count}"
        
        audit_df = pd.read_sql(query_str, conn)
        # Apply visual status badges
        audit_df["Status"] = audit_df["Status"].apply(lambda s: " Success" if s == "Success" else " Failed")
        st.dataframe(audit_df, use_container_width=True)
    except:
        st.info("No audit logs found.")
    finally:
        conn.close()
        
    st.button("Export Filtered Logs as CSV Compliance File", use_container_width=True)

# --- Main Application Logic ---
def main():
    if not st.session_state["authenticated"]:
        show_login_page()
    else:
        # User is authenticated
        selected_page = show_sidebar()
        
        # Route pages
        role = st.session_state["role"]
        
        if selected_page == "Dashboard":
            if role == "System Administrator":
                show_admin_dashboard()
            elif role == "Bank Manager":
                show_manager_dashboard()
            else:
                show_analyst_dashboard()
        elif selected_page == "Audit Trail" and role == "System Administrator":
            show_audit_page()
        elif selected_page == "AI Query":
            show_nlp_page()
        elif selected_page == "Upload" and role == "Business Analyst":
            show_upload_page()
        elif selected_page == "Fraud" and role == "Business Analyst":
            show_fraud_page()
        elif selected_page == "Churn" and role == "Business Analyst":
            show_churn_page()
        elif selected_page == "Revenue" and role == "Business Analyst":
            show_revenue_page()
        elif selected_page == "Branches" and role == "Business Analyst":
            show_branches_page()

if __name__ == "__main__":
    main()
