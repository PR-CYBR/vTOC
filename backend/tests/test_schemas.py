from __future__ import annotations

from datetime import UTC, datetime

from backend.app import schemas


class Attrs:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_station_read_from_attributes() -> None:
    payload = Attrs(
        id=1,
        slug="station-1",
        name="Station One",
        description="Primary station",
        timezone="UTC",
        telemetry_schema=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    station = schemas.StationRead.model_validate(payload)

    assert station.id == 1
    assert station.slug == "station-1"
    assert station.name == "Station One"


def test_activation_defaults() -> None:
    telemetry_source = schemas.TelemetrySourceCreate(
        slug="src-1",
        name="Source",
        source_type="test",
    )
    overlay = schemas.OverlayCreate(
        slug="overlay-1",
        name="Overlay",
        station_id=1,
        overlay_type="map",
    )

    assert telemetry_source.is_active is True
    assert overlay.is_active is True


def test_partial_update_models_allow_optional_fields() -> None:
    update = schemas.DeviceUpdate(name="Updated Device")

    assert update.name == "Updated Device"
    assert update.slug is None


def test_telemetry_event_update_excludes_station_id() -> None:
    assert "station_id" not in schemas.TelemetryEventUpdate.model_fields
