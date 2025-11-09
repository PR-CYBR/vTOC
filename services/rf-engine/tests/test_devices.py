"""Tests for device management."""

import pytest
from fastapi.testclient import TestClient

from rfengine.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_list_devices(client):
    """Test device list endpoint."""
    response = client.get("/api/v2/rf/devices/list")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert isinstance(data["devices"], list)
    
    # Should have at least mock device when SoapySDR not installed
    assert len(data["devices"]) >= 1
    
    device = data["devices"][0]
    assert "device_id" in device
    assert "driver" in device
    assert "label" in device
    assert "available" in device


def test_test_device(client):
    """Test device test endpoint."""
    # Test with mock device
    response = client.post("/api/v2/rf/devices/mock-rtl-0/test")
    assert response.status_code == 200
    data = response.json()
    assert "device_id" in data
    assert "status" in data
    assert data["device_id"] == "mock-rtl-0"
    # Will be error if SoapySDR not installed
    assert data["status"] in ["ok", "error"]


def test_test_device_invalid_id(client):
    """Test device test with invalid ID."""
    response = client.post("/api/v2/rf/devices/invalid/test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error"] is not None
