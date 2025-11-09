"""Tests for RF Engine FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from rfengine.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_healthz(client):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "station_id" in data
    assert "tx_enabled" in data


def test_metrics(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    # Check for some expected Prometheus metrics
    content = response.text
    assert "# HELP" in content or "# TYPE" in content


def test_rf_info(client):
    """Test RF info endpoint."""
    response = client.get("/api/v2/rf/info")
    assert response.status_code == 200
    data = response.json()
    assert "station_id" in data
    assert "division" in data
    assert "tx_enabled" in data
    assert "allowed_devices" in data
    assert "max_capture_seconds" in data
    assert "version" in data
    # TX should be disabled by default
    assert data["tx_enabled"] is False
