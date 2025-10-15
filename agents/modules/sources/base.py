import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

import requests


class TelemetrySourceConnector(ABC):
    """Base class for telemetry connectors."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"TelemetrySource[{self.name}]")
        self.backend_url = self.config.get("backend_url")
        self.session = requests.Session()

    @abstractmethod
    def fetch_online(self) -> Dict[str, Any]:
        """Fetch telemetry from a live service."""

    @abstractmethod
    def fetch_offline(self) -> Dict[str, Any]:
        """Fetch telemetry from an offline artefact (file/device)."""

    def poll(self) -> Optional[Dict[str, Any]]:
        """Dispatch to the correct fetch mode based on configuration."""

        mode = self.config.get("mode", "online").lower()
        try:
            if mode == "offline":
                self.logger.debug("Polling in offline mode")
                return self.fetch_offline()
            self.logger.debug("Polling in online mode")
            return self.fetch_online()
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.exception("Error polling telemetry: %s", exc)
            return None

    def push_event(self, payload: Dict[str, Any]) -> Optional[requests.Response]:
        """Send a telemetry payload to the backend ingest endpoint."""

        if not self.backend_url:
            self.logger.debug("No backend_url configured; skipping push")
            return None

        endpoint = f"{self.backend_url.rstrip('/')}/api/telemetry/ingest/{self.name}"
        envelope = {"event_time": datetime.utcnow().isoformat(), **payload}

        try:
            response = self.session.post(endpoint, json=envelope, timeout=10)
            response.raise_for_status()
            self.logger.info("Pushed telemetry event for %s", self.name)
            return response
        except requests.RequestException as exc:
            self.logger.error("Failed to push telemetry for %s: %s", self.name, exc)
            return None

