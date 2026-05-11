import streamlit as st
from pathlib import Path


def load_css():
    st.markdown("""
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"] { display: none !important; }
    [data-testid="stToolbar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    css_path = Path("assets/css/style.css")
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def apply_theme(theme: str = "light"):
    if theme == "dark":
        st.markdown("""
        <style>
        .stApp { background-color: #0f1117 !important; }
        .main .block-container { background-color: #0f1117; }
        .metric-card { background: #1e2130 !important; border-color: #f9a825; }
        .metric-card .metric-value { color: #90caf9 !important; }
        .metric-card .metric-label { color: #9e9e9e !important; }
        .info-card { background: #1e2130 !important; border-color: #2a2d3e !important; }
        .stDataFrame { filter: invert(0.9) hue-rotate(180deg); }
        </style>
        """, unsafe_allow_html=True)


def theme_toggle():
    current = st.session_state.get("theme", "light")
    label = "🌙" if current == "light" else "☀️"
    if st.sidebar.button(label + (" Dark Mode" if current == "light" else " Light Mode"),
                         use_container_width=True, key="theme_btn"):
        new_theme = "dark" if current == "light" else "light"
        st.session_state.theme = new_theme
        if st.session_state.get("user"):
            try:
                from db.connection import SessionLocal
                from services.auth_service import AuthService
                db = SessionLocal()
                AuthService.update_preferences(db, st.session_state.user["id"], theme=new_theme)
                db.close()
            except Exception:
                pass
        st.rerun()


def render_page_header(title: str, subtitle: str = "", icon: str = "", badge: str = ""):
    badge_html = f'<span class="header-badge">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="page-header">
        <h1>{icon}&nbsp; {title}</h1>
        {f'<p>{subtitle}</p>' if subtitle else ''}
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, icon: str = "📊",
                delta: str = "", delta_color: str = "normal"):
    if delta:
        color = "#2e7d32" if delta_color == "positive" else \
                "#c62828" if delta_color == "negative" else "#757575"
        arrow = "▲" if delta_color == "positive" else \
                "▼" if delta_color == "negative" else ""
        delta_html = f'<div class="metric-delta" style="color:{color}">{arrow} {delta}</div>'
    else:
        delta_html = ""

    st.markdown(f"""
    <div class="metric-card">
        <span class="metric-icon">{icon}</span>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <div class="footer">
        🏦 <strong>IntelliBank</strong> — AI-Powered Banking Data Analyst &nbsp;·&nbsp;
        Iqra University Final Year Project &nbsp;·&nbsp; v1.0.0
    </div>
    """, unsafe_allow_html=True)
