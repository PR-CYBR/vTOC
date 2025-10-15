from pathlib import Path
from typing import Any, Dict

import requests

from .base import TelemetrySourceConnector


class APRSSourceConnector(TelemetrySourceConnector):
    """Connector for APRS packet telemetry."""

    def fetch_online(self) -> Dict[str, Any]:
        igate_url = self.config.get("igate_url")
        if not igate_url:
            self.logger.warning("APRS connector missing igate_url configuration")
            return {}

        try:
            response = self.session.get(
                igate_url,
                params=self.config.get("params", {}),
                timeout=self.config.get("timeout", 10),
            )
            response.raise_for_status()
            return {"raw_data": response.text, "status": "received"}
        except requests.RequestException as exc:
            self.logger.error("Failed to fetch APRS data: %s", exc)
            return {}

    def fetch_offline(self) -> Dict[str, Any]:
        packet_log = self.config.get("packet_log")
        if not packet_log:
            self.logger.warning("APRS connector missing packet_log configuration")
            return {}

        path = Path(packet_log)
        if not path.exists():
            self.logger.error("APRS packet log does not exist: %s", path)
            return {}

        raw_data = path.read_text(encoding="utf-8", errors="ignore")
        return {"raw_data": raw_data, "status": "replayed"}

