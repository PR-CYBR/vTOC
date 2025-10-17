"""Configuration helpers for the ADS-B ingest proxy."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    backend_base_url: str = "http://backend:8000"
    telemetry_endpoint: str = "/api/v1/telemetry/events"
    telemetry_source_slug: str = "adsb-ingest"
    station_id: Optional[int] = None
    poll_interval_seconds: float = 2.0
    request_timeout: float = 5.0
    push_timeout: float = 5.0
    health_ttl_seconds: float = 30.0
    readsb_url: Optional[str] = "http://readsb:8080/data/aircraft.json"
    readsb_file: Optional[Path] = None
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        """Create a settings object from environment variables."""

        backend_base_url = os.getenv("BACKEND_BASE_URL", cls.backend_base_url)
        telemetry_endpoint = os.getenv(
            "TELEMETRY_ENDPOINT", cls.telemetry_endpoint
        )
        telemetry_source_slug = os.getenv(
            "TELEMETRY_SOURCE_SLUG", cls.telemetry_source_slug
        )
        station_id_raw = os.getenv("STATION_ID")
        station_id: Optional[int]
        if station_id_raw is None or station_id_raw == "":
            station_id = None
        else:
            try:
                station_id = int(station_id_raw)
            except ValueError:
                raise ValueError("STATION_ID must be an integer if provided") from None

        poll_interval_seconds = float(
            os.getenv("POLL_INTERVAL_SECONDS", cls.poll_interval_seconds)
        )
        request_timeout = float(os.getenv("REQUEST_TIMEOUT", cls.request_timeout))
        push_timeout = float(os.getenv("PUSH_TIMEOUT", cls.push_timeout))
        health_ttl_seconds = float(
            os.getenv("HEALTH_TTL_SECONDS", cls.health_ttl_seconds)
        )
        readsb_url = os.getenv("READSB_URL", cls.readsb_url)
        readsb_file_raw = os.getenv("READSB_FILE")
        readsb_file = Path(readsb_file_raw) if readsb_file_raw else None
        log_level = os.getenv("LOG_LEVEL", cls.log_level)

        return cls(
            backend_base_url=backend_base_url,
            telemetry_endpoint=telemetry_endpoint,
            telemetry_source_slug=telemetry_source_slug,
            station_id=station_id,
            poll_interval_seconds=poll_interval_seconds,
            request_timeout=request_timeout,
            push_timeout=push_timeout,
            health_ttl_seconds=health_ttl_seconds,
            readsb_url=readsb_url,
            readsb_file=readsb_file,
            log_level=log_level,
        )


__all__ = ["Settings"]
