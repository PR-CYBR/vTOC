"""Parsing utilities for GPS NMEA sentences."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pynmea2

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GPSFix:
    """Normalized GPS fix information extracted from NMEA sentences."""

    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    speed_kmh: Optional[float] = None
    timestamp: Optional[datetime] = None

    def to_payload(self) -> dict[str, float | str]:
        """Convert the fix into a JSON-serializable payload."""

        payload: dict[str, float | str] = {
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
        if self.altitude_m is not None:
            payload["altitude_m"] = self.altitude_m
        if self.speed_kmh is not None:
            payload["speed_kmh"] = self.speed_kmh
        if self.timestamp is not None:
            payload["timestamp"] = self.timestamp.isoformat()
        return payload


def _coerce_float(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _derive_timestamp(message: pynmea2.nmea.NMEASentence) -> Optional[datetime]:
    datestamp = getattr(message, "datestamp", None)
    timestamp = getattr(message, "timestamp", None)
    if datestamp and timestamp:
        return datetime.combine(datestamp, timestamp)
    return None


def parse_nmea_sentence(sentence: str) -> Optional[GPSFix]:
    """Parse a raw NMEA sentence into a :class:`GPSFix` instance.

    Returns ``None`` when the sentence cannot be parsed or does not contain
    positional information.
    """

    sentence = sentence.strip()
    if not sentence:
        return None

    try:
        message = pynmea2.parse(sentence, check=True)
    except (pynmea2.nmea.ParseError, pynmea2.nmea.ChecksumError, ValueError) as exc:
        logger.debug("Failed to parse NMEA sentence %r: %s", sentence, exc)
        return None

    latitude = _coerce_float(getattr(message, "latitude", None))
    longitude = _coerce_float(getattr(message, "longitude", None))
    if latitude is None or longitude is None:
        return None

    altitude = _coerce_float(getattr(message, "altitude", None))

    speed_knots = _coerce_float(
        getattr(message, "spd_over_grnd", None)
        or getattr(message, "speed", None)
        or getattr(message, "spd_over_ground", None)
    )
    speed_kmh = speed_knots * 1.852 if speed_knots is not None else None

    timestamp = _derive_timestamp(message)

    return GPSFix(
        latitude=latitude,
        longitude=longitude,
        altitude_m=altitude,
        speed_kmh=speed_kmh,
        timestamp=timestamp,
    )
