"""Tests for POI and IMEI watchlist API endpoints."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import schemas


client = TestClient(app)


@pytest.fixture
def mock_poi_data():
    """Sample POI data for testing."""
    return {
        "name": "Test Subject",
        "category": "person",
        "risk_level": "watch",
        "notes": "Test notes",
        "is_active": True,
    }


@pytest.fixture
def mock_imei_data():
    """Sample IMEI watchlist data for testing."""
    return {
        "identifier_value": "123456789012345",
        "list_type": "blacklist",
        "label": "Test Device",
        "linked_poi_id": None,
    }


class TestPOISchemas:
    """Test POI schema validation."""

    def test_poi_create_schema_valid(self, mock_poi_data):
        """Test that valid POI data passes schema validation."""
        poi = schemas.PoiCreate(**mock_poi_data)
        assert poi.name == "Test Subject"
        assert poi.category == "person"
        assert poi.risk_level == "watch"

    def test_poi_create_schema_defaults(self):
        """Test POI schema default values."""
        poi = schemas.PoiCreate(name="Test")
        assert poi.category == "person"
        assert poi.risk_level == "info"
        assert poi.is_active is True

    def test_poi_identifier_create_schema(self):
        """Test POI identifier schema validation."""
        identifier = schemas.PoiIdentifierCreate(
            poi_id=1,
            identifier_type="imei",
            identifier_value="123456789012345",
            is_primary=True,
        )
        assert identifier.poi_id == 1
        assert identifier.identifier_type == "imei"
        assert identifier.is_primary is True


class TestIMEIWatchlistSchemas:
    """Test IMEI watchlist schema validation."""

    def test_imei_watch_entry_create_schema_valid(self, mock_imei_data):
        """Test that valid IMEI data passes schema validation."""
        entry = schemas.ImeiWatchEntryCreate(**mock_imei_data)
        assert entry.identifier_value == "123456789012345"
        assert entry.list_type == "blacklist"
        assert entry.label == "Test Device"

    def test_imei_watch_entry_list_type_validation(self):
        """Test that list_type must be whitelist or blacklist."""
        # Valid values
        entry1 = schemas.ImeiWatchEntryCreate(
            identifier_value="123", list_type="whitelist"
        )
        assert entry1.list_type == "whitelist"
        
        entry2 = schemas.ImeiWatchEntryCreate(
            identifier_value="123", list_type="blacklist"
        )
        assert entry2.list_type == "blacklist"

        # Invalid value should fail pattern validation
        with pytest.raises(ValueError):
            schemas.ImeiWatchEntryCreate(
                identifier_value="123", list_type="invalid"
            )


class TestStationTimelinePoiAlertEntry:
    """Test POI alert timeline entry schema."""

    def test_poi_alert_entry_schema(self):
        """Test POI alert entry with required fields."""
        from datetime import datetime
        
        entry = schemas.StationTimelinePoiAlertEntry(
            occurred_at=datetime.utcnow(),
            event_id=123,
            alert_type="imei_blacklist_hit",
            imei="123456789012345",
            poi_id=1,
            poi_name="Suspect Device",
            station_callsign="TOC-S1",
        )
        assert entry.entry_type == "poi_imei_alert"
        assert entry.alert_type == "imei_blacklist_hit"
        assert entry.imei == "123456789012345"
        assert entry.poi_id == 1

    def test_poi_alert_entry_optional_fields(self):
        """Test POI alert entry with optional fields."""
        from datetime import datetime
        
        entry = schemas.StationTimelinePoiAlertEntry(
            occurred_at=datetime.utcnow(),
            event_id=123,
            alert_type="imei_whitelist_seen",
            imei="123456789012345",
        )
        assert entry.entry_type == "poi_imei_alert"
        assert entry.poi_id is None
        assert entry.poi_name is None
        assert entry.station_callsign is None


class TestTelemetryEventWithIMEI:
    """Test telemetry event schema with IMEI data."""

    def test_telemetry_event_with_imei_payload(self):
        """Test creating telemetry event with IMEI in payload."""
        event = schemas.TelemetryEventCreate(
            source_slug="test-source",
            payload={
                "imei": "123456789012345",
                "device_type": "mobile",
            }
        )
        assert event.payload["imei"] == "123456789012345"

    def test_telemetry_event_with_enriched_poi_data(self):
        """Test telemetry event with POI enrichment."""
        from datetime import datetime
        
        event = schemas.TelemetryEventRead(
            id=1,
            status="imei_blacklist_hit",
            received_at=datetime.utcnow(),
            payload={
                "imei": "123456789012345",
                "imei_watchlist_hit": True,
                "imei_list_type": "blacklist",
                "poi_id": 1,
                "poi_name": "Suspect Device",
                "poi_risk_level": "hostile",
            }
        )
        assert event.status == "imei_blacklist_hit"
        assert event.payload["imei_watchlist_hit"] is True
        assert event.payload["poi_id"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
