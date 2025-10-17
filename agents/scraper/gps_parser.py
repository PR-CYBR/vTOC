"""Helpers for parsing GPS telemetry feeds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List


@dataclass(slots=True)
class GpsFix:
    """Represents a normalized GPS fix."""

    latitude: float
    longitude: float
    timestamp: datetime
    altitude_m: float | None = None
    speed_knots: float | None = None
    course: float | None = None

    def as_geojson_feature(self) -> dict[str, object]:
        """Return a GeoJSON feature for quick visualization during tests."""

        properties: dict[str, object] = {
            "timestamp": self.timestamp.isoformat(),
        }
        if self.altitude_m is not None:
            properties["altitude_m"] = round(self.altitude_m, 2)
        if self.speed_knots is not None:
            properties["speed_knots"] = round(self.speed_knots, 2)
        if self.course is not None:
            properties["course"] = round(self.course, 2)
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude],
            },
            "properties": properties,
        }


def _validate_checksum(sentence: str) -> str:
    body, _, checksum = sentence.partition("*")
    if not checksum:
        return body
    payload = body[1:] if body.startswith("$") else body
    value = 0
    for char in payload:
        value ^= ord(char)
    expected = int(checksum.strip(), 16)
    if value != expected:
        raise ValueError("Invalid NMEA checksum")
    return body


def _parse_latitude(value: str, direction: str) -> float:
    if not value or not direction:
        raise ValueError("Latitude components missing")
    degrees = int(value[:2])
    minutes = float(value[2:])
    coord = degrees + minutes / 60
    if direction.upper() == "S":
        coord *= -1
    return coord


def _parse_longitude(value: str, direction: str) -> float:
    if not value or not direction:
        raise ValueError("Longitude components missing")
    degrees = int(value[:3])
    minutes = float(value[3:])
    coord = degrees + minutes / 60
    if direction.upper() == "W":
        coord *= -1
    return coord


def _parse_datetime(date_str: str | None, time_str: str) -> datetime:
    if not time_str:
        raise ValueError("NMEA sentence missing time component")
    hours = int(time_str[0:2])
    minutes = int(time_str[2:4])
    seconds = float(time_str[4:])
    microseconds = int((seconds % 1) * 1_000_000)
    seconds_int = int(seconds)

    if date_str:
        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year_suffix = int(date_str[4:6])
        if year_suffix >= 80:
            year = 1900 + year_suffix
        else:
            year = 2000 + year_suffix
        base = datetime(year, month, day, hours, minutes, seconds_int, tzinfo=timezone.utc)
    else:
        now = datetime.now(tz=timezone.utc)
        base = now.replace(hour=hours, minute=minutes, second=seconds_int, microsecond=0)

    return base.replace(microsecond=microseconds)


def parse_nmea_sentence(sentence: str) -> GpsFix:
    """Parse a single NMEA sentence into a :class:`GpsFix`."""

    normalized = _validate_checksum(sentence.strip())
    parts = normalized.split(",")
    if not parts or len(parts[0]) < 6:
        raise ValueError("Unsupported NMEA sentence")

    sentence_type = parts[0][3:6]

    if sentence_type == "RMC":
        status = parts[2]
        if status != "A":
            raise ValueError("GPS fix not active")
        latitude = _parse_latitude(parts[3], parts[4])
        longitude = _parse_longitude(parts[5], parts[6])
        speed = float(parts[7]) if parts[7] else None
        course = float(parts[8]) if parts[8] else None
        timestamp = _parse_datetime(parts[9], parts[1])
        return GpsFix(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            speed_knots=speed,
            course=course,
        )

    if sentence_type == "GGA":
        fix_quality = parts[6]
        if fix_quality == "0":
            raise ValueError("No GPS fix available")
        latitude = _parse_latitude(parts[2], parts[3])
        longitude = _parse_longitude(parts[4], parts[5])
        altitude = float(parts[9]) if parts[9] else None
        timestamp = _parse_datetime(None, parts[1])
        return GpsFix(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            altitude_m=altitude,
        )

    raise ValueError(f"Unsupported NMEA sentence type: {sentence_type}")


def parse_nmea_log(lines: Iterable[str]) -> List[GpsFix]:
    """Parse multiple NMEA sentences and return valid fixes."""

    fixes: List[GpsFix] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            fix = parse_nmea_sentence(stripped)
        except ValueError:
            continue
        fixes.append(fix)
    return fixes


def load_nmea_file(path: str | Path) -> List[GpsFix]:
    """Convenience helper used by tests to parse fixture logs."""

    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return parse_nmea_log(handle)


__all__ = ["GpsFix", "parse_nmea_sentence", "parse_nmea_log", "load_nmea_file"]
