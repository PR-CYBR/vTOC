from pathlib import Path
from typing import Any, Dict

import requests

from .base import TelemetrySourceConnector


class MeshtasticSourceConnector(TelemetrySourceConnector):
    """Connector for Meshtastic mesh telemetry."""

    def fetch_online(self) -> Dict[str, Any]:
        http_bridge = self.config.get("http_bridge")
        if not http_bridge:
            self.logger.warning("Meshtastic connector missing http_bridge configuration")
            return {}

        try:
            response = self.session.get(
                http_bridge,
                timeout=self.config.get("timeout", 10),
            )
            response.raise_for_status()
            return {"payload": response.json(), "status": "received"}
        except requests.RequestException as exc:
            self.logger.error("Failed to fetch Meshtastic data: %s", exc)
            return {}

    def fetch_offline(self) -> Dict[str, Any]:
        json_log = self.config.get("json_log")
        if not json_log:
            self.logger.warning("Meshtastic connector missing json_log configuration")
            return {}

        path = Path(json_log)
        if not path.exists():
            self.logger.error("Meshtastic JSON log does not exist: %s", path)
            return {}

        raw_data = path.read_text(encoding="utf-8", errors="ignore")
        return {"raw_data": raw_data, "status": "replayed"}

