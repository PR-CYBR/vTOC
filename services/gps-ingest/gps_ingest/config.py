"""Configuration loading for the GPS ingestion service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Optional


@dataclass(slots=True)
class Config:
    """Runtime configuration values for the GPS ingestion service."""

    serial_port: str
    baud_rate: int
    api_url: str
    api_token: Optional[str]
    reconnect_initial: float = 1.0
    reconnect_max_delay: float = 30.0
    reconnect_max_attempts: Optional[int] = None
    serial_timeout: float = 1.0

    @property
    def headers(self) -> dict[str, str]:
        """Return default HTTP headers for publishing."""

        headers = {"User-Agent": "gps-ingest/0.1"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers


def _get_env(env: Mapping[str, str], key: str) -> str:
    try:
        value = env[key]
    except KeyError as exc:
        raise ValueError(f"Missing required environment variable: {key}") from exc
    if not value:
        raise ValueError(f"Environment variable {key} cannot be empty")
    return value


def load_config(env: Mapping[str, str] | None = None) -> Config:
    """Load configuration from environment variables.

    Parameters
    ----------
    env:
        Mapping of environment variables. Defaults to :data:`os.environ`.

    Returns
    -------
    Config
        Populated configuration dataclass.

    Raises
    ------
    ValueError
        If any required configuration is missing or invalid.
    """

    env = env or os.environ

    serial_port = _get_env(env, "GPS_SERIAL")

    baud_raw = env.get("GPS_BAUD", "9600")
    try:
        baud_rate = int(baud_raw)
    except ValueError as exc:
        raise ValueError("GPS_BAUD must be an integer") from exc
    if baud_rate <= 0:
        raise ValueError("GPS_BAUD must be positive")

    api_url = _get_env(env, "GPS_API_URL")
    api_token = env.get("GPS_API_TOKEN") or None

    reconnect_initial = float(env.get("GPS_RECONNECT_INITIAL", 1.0))
    reconnect_max_delay = float(env.get("GPS_RECONNECT_MAX_DELAY", 30.0))
    reconnect_max_attempts_raw = env.get("GPS_RECONNECT_MAX_ATTEMPTS")
    reconnect_max_attempts = (
        int(reconnect_max_attempts_raw)
        if reconnect_max_attempts_raw not in (None, "")
        else None
    )
    serial_timeout = float(env.get("GPS_SERIAL_TIMEOUT", 1.0))

    return Config(
        serial_port=serial_port,
        baud_rate=baud_rate,
        api_url=api_url,
        api_token=api_token,
        reconnect_initial=reconnect_initial,
        reconnect_max_delay=reconnect_max_delay,
        reconnect_max_attempts=reconnect_max_attempts,
        serial_timeout=serial_timeout,
    )
