from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.scraper.adsb_proxy import AdsbContact, AdsbProxy  # noqa: E402


@pytest.fixture()
def proxy() -> AdsbProxy:
    return AdsbProxy(station_slug="test-station", source_slug="adsb-test")


def test_normalize_state_returns_contact(proxy: AdsbProxy) -> None:
    state = {
        "hex": "abc123",
        "lat": 40.7128,
        "lon": -74.0060,
        "flight": "TEST123 ",
        "alt_baro": 32000,
        "track": 270.0,
        "gs": 430.5,
        "timestamp": 1_700_000_000,
    }

    contact = proxy.normalize_state(state)
    assert isinstance(contact, AdsbContact)
    assert contact.callsign == "TEST123"
    assert contact.altitude_ft == pytest.approx(32000)
    assert contact.ground_speed == pytest.approx(430.5)
    assert contact.track == pytest.approx(270.0)
    assert contact.received_at == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)

    event = proxy.to_backend_event(contact)
    assert event["station_slug"] == "test-station"
    assert event["source_slug"] == "adsb-test"
    assert event["latitude"] == pytest.approx(40.7128)
    assert event["payload"]["position"]["lon"] == pytest.approx(-74.0060)


def test_normalize_state_rejects_incomplete_data(proxy: AdsbProxy) -> None:
    assert proxy.normalize_state({"hex": "abc123"}) is None
    assert proxy.normalize_state({"hex": "abc123", "lat": 10.0}) is None
    assert proxy.normalize_state({"lat": 10.0, "lon": 20.0}) is None


def test_normalize_capture_filters_invalid_entries(proxy: AdsbProxy) -> None:
    states = [
        {"hex": "abc123", "lat": 40.0, "lon": -70.0, "timestamp": 1_700_000_010},
        {"hex": "", "lat": 30.0, "lon": 10.0},
        {"hex": "def456", "lat": None, "lon": 20.0},
    ]

    events = proxy.normalize_capture(states)
    assert len(events) == 1
    event = events[0]
    assert event["payload"]["icao"] == "ABC123"
