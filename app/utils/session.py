import base64
import json
from datetime import datetime
import streamlit as st
from db.connection import SessionLocal
from db.models import UserRole, User, UserSession
from services.auth_service import has_permission
from config.security import decode_token


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
    """
    Restore session from URL params on browser refresh.
    Fast path: decode JWT directly (no DB call needed).
    Fallback: DB lookup if JWT is missing but hash is present.
    """
    token = st.query_params.get("_s", "")
    if not token:
        return

    # ── Fast path: verify JWT signature + decode user data from _u ───────────
    payload = decode_token(token)
    if payload:
        user_b64 = st.query_params.get("_u", "")
        if user_b64:
            try:
                # add padding if stripped by URL encoding
                padded = user_b64 + "=" * (4 - len(user_b64) % 4)
                user_data = json.loads(base64.urlsafe_b64decode(padded).decode())
                st.session_state.authenticated = True
                st.session_state.token         = token
                st.session_state.user          = user_data
                st.session_state.theme         = user_data.get("theme_preference", "light")
                st.session_state.language      = user_data.get("preferred_language", "en")
                return
            except Exception:
                pass

    # ── Fallback: DB lookup (handles older sessions that only stored a hash) ──
    try:
        db = SessionLocal()
        session = db.query(UserSession).filter(
            UserSession.token_hash == token,
            UserSession.is_active  == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        if session:
            user = db.query(User).filter(User.id == session.user_id).first()
            if user:
                _set_auth(token, {
                    "id":                 user.id,
                    "username":           user.username,
                    "email":              user.email,
                    "full_name":          user.full_name or user.username,
                    "role":               user.role.value,
                    "branch_id":          user.branch_id,
                    "preferred_language": user.preferred_language or "en",
                    "theme_preference":   user.theme_preference or "light",
                })
        db.close()
    except Exception:
        pass


def _set_auth(token: str, user_data: dict):
    st.session_state.authenticated = True
    st.session_state.token         = token
    st.session_state.user          = user_data
    st.session_state.theme         = user_data.get("theme_preference", "light")
    st.session_state.language      = user_data.get("preferred_language", "en")


def login(token: str, user_data: dict):
    _set_auth(token, user_data)
    # Store full JWT in _s (verifiable without DB on refresh)
    st.query_params["_s"] = token
    # Store user data in _u (base64 JSON) for instant no-DB restore
    st.query_params["_u"] = base64.urlsafe_b64encode(
        json.dumps(user_data).encode()
    ).decode().rstrip("=")


def logout():
    for param in ["_s", "_u"]:
        if param in st.query_params:
            del st.query_params[param]
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("main.py")


def require_auth():
    init_session()
    if not st.session_state.get("authenticated"):
        st.switch_page("main.py")

    # Re-stamp both params after st.switch_page() which drops URL params
    token = st.session_state.get("token")
    user  = st.session_state.get("user")
    if token and not st.query_params.get("_s"):
        st.query_params["_s"] = token
    if user and not st.query_params.get("_u"):
        st.query_params["_u"] = base64.urlsafe_b64encode(
            json.dumps(user).encode()
        ).decode().rstrip("=")

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
