import streamlit as st
from config.security import decode_token
from db.connection import SessionLocal
from db.models import User, UserRole
from services.auth_service import has_permission


def init_session():
    defaults = {
        "authenticated": False,
        "user": None,
        "token": None,
        "theme": "light",
        "language": "en",
        "tour_completed": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def login(token: str, user_data: dict):
    st.session_state.authenticated = True
    st.session_state.token = token
    st.session_state.user = user_data
    st.session_state.theme = user_data.get("theme_preference", "light")
    st.session_state.language = user_data.get("preferred_language", "en")


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("main.py")


def require_auth():
    init_session()
    if not st.session_state.authenticated:
        st.switch_page("main.py")
    return st.session_state.user


def require_permission(permission: str):
    user = require_auth()
    role = UserRole(user["role"])
    if not has_permission(role, permission):
        st.error(f"Access denied. Your role ({user['role']}) does not have '{permission}' permission.")
        st.stop()
    return user


def get_db_session():
    return SessionLocal()


def current_language() -> str:
    return st.session_state.get("language", "en")


def current_theme() -> str:
    return st.session_state.get("theme", "light")
