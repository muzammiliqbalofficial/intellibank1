import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.security import hash_password, verify_password, create_access_token, decode_token
from services.auth_service import has_permission
from db.models import UserRole


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        hashed = hash_password("testpass")
        assert verify_password("testpass", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("testpass")
        assert verify_password("wrongpass", hashed) is False

    def test_unique_hashes(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # bcrypt uses random salts


class TestJWT:
    def test_create_and_decode_token(self):
        data = {"sub": "42", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "42"
        assert decoded["role"] == "admin"

    def test_invalid_token_returns_none(self):
        result = decode_token("not.a.valid.token")
        assert result is None

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "1"})
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None


class TestRBAC:
    def test_admin_has_all_permissions(self):
        assert has_permission(UserRole.ADMIN, "manage_users") is True
        assert has_permission(UserRole.ADMIN, "view_audit_logs") is True
        assert has_permission(UserRole.ADMIN, "view_fraud") is True

    def test_analyst_cannot_manage_users(self):
        assert has_permission(UserRole.BUSINESS_ANALYST, "manage_users") is False
        assert has_permission(UserRole.BUSINESS_ANALYST, "view_audit_logs") is False

    def test_analyst_can_view_fraud(self):
        assert has_permission(UserRole.BUSINESS_ANALYST, "view_fraud") is True

    def test_manager_can_resolve_alerts(self):
        assert has_permission(UserRole.BANK_MANAGER, "resolve_alerts") is True

    def test_unknown_permission_returns_false(self):
        assert has_permission(UserRole.ADMIN, "nonexistent_permission") is False
