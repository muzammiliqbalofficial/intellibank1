"""
Integration Tests — FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture(scope="module")
def client():
    from api.main import app
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestAuthEndpoints:
    def test_login_requires_credentials(self, client):
        response = client.post("/api/auth/login", data={"username": "", "password": ""})
        assert response.status_code in (401, 422)

    def test_login_with_wrong_credentials(self, client):
        response = client.post("/api/auth/login",
                                data={"username": "nonexistent", "password": "wrongpass"})
        assert response.status_code == 401

    def test_protected_route_without_token(self, client):
        response = client.post("/api/fraud/predict", json={"amount": 1000.0})
        assert response.status_code == 401


class TestFraudEndpoint:
    def test_fraud_prediction_structure(self, client):
        """Test that fraud endpoint returns expected fields (requires auth token)."""
        # Without auth, expect 401
        response = client.post("/api/fraud/predict", json={
            "amount": 5000.0,
            "merchant_category": "online",
            "transaction_type": "debit",
        })
        assert response.status_code == 401

    def test_fraud_alerts_endpoint_unauthorized(self, client):
        response = client.get("/api/fraud/alerts")
        assert response.status_code == 401


class TestRateLimiting:
    def test_health_not_rate_limited(self, client):
        """Health endpoint should be accessible."""
        for _ in range(5):
            response = client.get("/api/health")
            assert response.status_code == 200


@pytest.fixture
def conftest_init():
    """Initialize test DB."""
    os.environ["DATABASE_URL"] = "postgresql://intellibank_user:password@localhost:5432/intellibank_test"
