import hashlib
from datetime import datetime
import streamlit as st
from db.connection import SessionLocal
from db.models import UserRole, User, UserSession
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

    if not st.session_state.get("authenticated"):
        _restore_from_url()


def _restore_from_url():
    token_hash = st.query_params.get("_s", "")
    if not token_hash:
        return
    try:
        db = SessionLocal()
        session = db.query(UserSession).filter(
            UserSession.token_hash == token_hash,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        if session:
            user = db.query(User).filter(User.id == session.user_id).first()
            if user:
                st.session_state.authenticated = True
                st.session_state.token = token_hash
                st.session_state.user = {
                    "id":                 user.id,
                    "username":           user.username,
                    "email":              user.email,
                    "full_name":          user.full_name or user.username,
                    "role":               user.role.value,
                    "branch_id":          user.branch_id,
                    "preferred_language": user.preferred_language or "en",
                    "theme_preference":   user.theme_preference or "light",
                }
                st.session_state.theme    = user.theme_preference or "light"
                st.session_state.language = user.preferred_language or "en"
        db.close()
    except Exception:
        pass


def login(token: str, user_data: dict):
    st.session_state.authenticated = True
    st.session_state.token = token
    st.session_state.user = user_data
    st.session_state.theme    = user_data.get("theme_preference", "light")
    st.session_state.language = user_data.get("preferred_language", "en")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    st.query_params["_s"] = token_hash


def logout():
    if "_s" in st.query_params:
        del st.query_params["_s"]
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("main.py")


def require_auth():
    init_session()
    if not st.session_state.get("authenticated"):
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
