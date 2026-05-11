from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from db.models import User, UserSession, AuditLog, UserRole
from config.security import hash_password, verify_password, create_access_token, create_refresh_token
from config.settings import settings
import hashlib
import secrets


class AuthService:

    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str,
                    full_name: str, role: UserRole, branch_id: Optional[int] = None) -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            branch_id=branch_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        AuditService.log(db, user_id=user.id, action="USER_CREATED",
                         resource="users", resource_id=str(user.id))
        return user

    @staticmethod
    def authenticate(db: Session, username: str, password: str,
                     ip_address: str = None, user_agent: str = None) -> Optional[dict]:
        user = db.query(User).filter(
            (User.username == username) | (User.email == username),
            User.is_active == True
        ).first()

        if not user or not verify_password(password, user.hashed_password):
            AuditService.log(db, action="LOGIN_FAILED", resource="auth",
                             details={"username": username}, ip_address=ip_address,
                             is_success=False)
            return None

        access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Store session
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        db.add(session)

        user.last_login = datetime.utcnow()
        db.commit()

        AuditService.log(db, user_id=user.id, action="LOGIN_SUCCESS", resource="auth",
                         ip_address=ip_address, user_agent=user_agent)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "branch_id": user.branch_id,
                "preferred_language": user.preferred_language,
                "theme_preference": user.theme_preference,
            }
        }

    @staticmethod
    def logout(db: Session, token: str, user_id: int):
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session = db.query(UserSession).filter_by(token_hash=token_hash, is_active=True).first()
        if session:
            session.is_active = False
            db.commit()
        AuditService.log(db, user_id=user_id, action="LOGOUT", resource="auth")

    @staticmethod
    def update_preferences(db: Session, user_id: int, language: str = None, theme: str = None):
        user = db.query(User).filter_by(id=user_id).first()
        if language:
            user.preferred_language = language
        if theme:
            user.theme_preference = theme
        db.commit()


# RBAC permission map
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "manage_users", "view_all_branches", "manage_system",
        "view_fraud", "view_churn", "view_forecast", "upload_data",
        "run_nlp", "generate_reports", "view_audit_logs",
        "resolve_alerts", "configure_alerts",
    },
    UserRole.BANK_MANAGER: {
        "view_all_branches", "view_fraud", "view_churn", "view_forecast",
        "upload_data", "run_nlp", "generate_reports", "resolve_alerts",
    },
    UserRole.BUSINESS_ANALYST: {
        "view_fraud", "view_churn", "view_forecast",
        "upload_data", "run_nlp", "generate_reports",
    },
}


def has_permission(role: UserRole, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


class AuditService:

    @staticmethod
    def log(db: Session, action: str, user_id: int = None, resource: str = None,
            resource_id: str = None, details: dict = None, ip_address: str = None,
            user_agent: str = None, is_success: bool = True, error_message: str = None):
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            is_success=is_success,
            error_message=error_message,
        )
        db.add(entry)
        try:
            db.commit()
        except Exception:
            db.rollback()

    @staticmethod
    def get_logs(db: Session, user_id: int = None, action: str = None,
                 resource: str = None, limit: int = 100, offset: int = 0):
        query = db.query(AuditLog)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action.ilike(f"%{action}%"))
        if resource:
            query = query.filter(AuditLog.resource == resource)
        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
