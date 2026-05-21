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
        /* ── Backgrounds ── */
        .stApp { background-color: #0f1117 !important; }
        .main .block-container { background-color: #0f1117 !important; }

        /* ── Body text ── */
        .stApp p,
        .stApp li,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li { color: #e0e0e0 !important; }

        /* ── Headings ── */
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stHeadingWithActionElements"] { color: #ffffff !important; }

        /* ── Captions & secondary text ── */
        [data-testid="stText"],
        [data-testid="stCaption"] { color: #b0b0b0 !important; }

        /* ── Form labels ── */
        .stApp label,
        [data-testid="stTextInput"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stSelectbox"] label,
        [data-testid="stSlider"] label,
        [data-testid="stRadio"] label,
        [data-testid="stCheckbox"] label,
        [data-testid="stTextArea"] label,
        [data-testid="stFileUploader"] label { color: #e0e0e0 !important; }

        /* ── Input fields ── */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            background-color: #1e2130 !important;
            color: #e0e0e0 !important;
            border-color: #3a3d4e !important;
        }

        /* ── Select boxes ── */
        [data-baseweb="select"] div,
        [data-baseweb="select"] span { color: #e0e0e0 !important; }

        /* ── Tabs ── */
        [data-baseweb="tab"] { color: #b0b0b0 !important; }
        [aria-selected="true"][data-baseweb="tab"] { color: #ffffff !important; }
        [data-baseweb="tab-list"] { background-color: #1e2130 !important; }

        /* ── Custom metric cards ── */
        .metric-card { background: #1e2130 !important; border-color: #f9a825 !important; }
        .metric-card .metric-value { color: #90caf9 !important; }
        .metric-card .metric-label { color: #9e9e9e !important; }
        .info-card { background: #1e2130 !important; border-color: #2a2d3e !important; }

        /* ── Streamlit metric widget ── */
        [data-testid="stMetricValue"] { color: #90caf9 !important; }
        [data-testid="stMetricLabel"] { color: #b0b0b0 !important; }

        /* ── Dividers & form borders ── */
        hr { border-color: #2a2d3e !important; }
        [data-testid="stForm"] { border-color: #2a2d3e !important; }

        /* ── Alert boxes ── */
        [data-testid="stAlert"] { background-color: #1e2130 !important; color: #e0e0e0 !important; }

        /* ── DataFrames ── */
        .stDataFrame { filter: invert(0.9) hue-rotate(180deg); }

        /* ── Page header (custom component) ── */
        .page-header h1 { color: #ffffff !important; }
        .page-header p  { color: #b0b0b0 !important; }

        /* ── Footer ── */
        .footer { color: #9e9e9e !important; border-color: #2a2d3e !important; }
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
