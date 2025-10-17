"""Utility helpers for normalizing ADS-B telemetry feeds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, List, Optional


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value)
        except ValueError:
            return None
    return None


@dataclass(slots=True)
class AdsbContact:
    """Normalized representation of an ADS-B contact."""

    icao_address: str
    latitude: float
    longitude: float
    received_at: datetime
    callsign: str | None = None
    altitude_ft: float | None = None
    ground_speed: float | None = None
    track: float | None = None

    def to_event_payload(self) -> dict[str, Any]:
        """Produce a JSON serialisable payload for backend ingestion."""

        payload: dict[str, Any] = {
            "icao": self.icao_address,
            "position": {
                "lat": round(self.latitude, 6),
                "lon": round(self.longitude, 6),
            },
            "received_at": self.received_at.isoformat(),
        }
        if self.callsign:
            payload["callsign"] = self.callsign
        if self.altitude_ft is not None:
            payload["altitude_ft"] = round(self.altitude_ft, 2)
        if self.ground_speed is not None:
            payload.setdefault("velocity", {})["ground_speed"] = round(self.ground_speed, 2)
        if self.track is not None:
            payload.setdefault("velocity", {})["track"] = round(self.track, 2)
        return payload


class AdsbProxy:
    """Transforms vendor specific ADS-B payloads into backend friendly events."""

    def __init__(self, *, station_slug: str, source_slug: str = "adsb-proxy") -> None:
        self.station_slug = station_slug
        self.source_slug = source_slug

    def normalize_state(self, state: dict[str, Any]) -> Optional[AdsbContact]:
        icao = str(state.get("hex") or state.get("icao") or "").strip().upper()
        if not icao:
            return None

        latitude = _to_float(state.get("lat"))
        longitude = _to_float(state.get("lon"))
        if latitude is None or longitude is None:
            return None

        callsign = state.get("flight") or state.get("callsign")
        if isinstance(callsign, str):
            callsign = callsign.strip() or None
        else:
            callsign = None

        altitude_ft = _to_float(state.get("alt_baro") or state.get("altitude"))
        ground_speed = _to_float(state.get("gs") or state.get("speed"))
        track = _to_float(state.get("track"))

        timestamp_value = state.get("timestamp") or state.get("seen_pos") or state.get("seen")
        if isinstance(timestamp_value, (int, float)):
            received_at = datetime.fromtimestamp(float(timestamp_value), tz=timezone.utc)
        else:
            received_at = datetime.now(tz=timezone.utc)

        return AdsbContact(
            icao_address=icao,
            latitude=float(latitude),
            longitude=float(longitude),
            callsign=callsign,
            altitude_ft=altitude_ft,
            ground_speed=ground_speed,
            track=track,
            received_at=received_at,
        )

    def to_backend_event(self, contact: AdsbContact) -> dict[str, Any]:
        payload = contact.to_event_payload()
        return {
            "station_slug": self.station_slug,
            "source_slug": self.source_slug,
            "event_time": payload["received_at"],
            "latitude": payload["position"]["lat"],
            "longitude": payload["position"]["lon"],
            "payload": payload,
        }

    def normalize_capture(self, states: Iterable[dict[str, Any]]) -> List[dict[str, Any]]:
        events: List[dict[str, Any]] = []
        for state in states:
            contact = self.normalize_state(state)
            if contact is None:
                continue
            events.append(self.to_backend_event(contact))
        return events


__all__ = ["AdsbProxy", "AdsbContact"]
