"""Tests for Health API Endpoint.

TDD: RED -> GREEN -> REFACTOR
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestHealthEndpoint:
    """Test cases for health endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check_returns_ok(self, client):
        """Test health check returns OK status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "PokerVOD API"
        assert "version" in data
        assert "docs" in data
