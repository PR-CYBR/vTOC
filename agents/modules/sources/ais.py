from pathlib import Path
from typing import Any, Dict

import requests

from .base import TelemetrySourceConnector


class AISSourceConnector(TelemetrySourceConnector):
    """Connector for AIS maritime telemetry feeds."""

    def fetch_online(self) -> Dict[str, Any]:
        endpoint = self.config.get("api_url")
        token = self.config.get("api_token")
        if not endpoint:
            self.logger.warning("AIS connector missing api_url configuration")
            return {}

        headers = self.config.get("headers", {})
        if token:
            headers.setdefault("Authorization", f"Bearer {token}")

        try:
            response = self.session.get(
                endpoint,
                params=self.config.get("params", {}),
                headers=headers,
                timeout=self.config.get("timeout", 10),
            )
            response.raise_for_status()
            return {"payload": response.json(), "status": "received"}
        except requests.RequestException as exc:
            self.logger.error("Failed to fetch AIS data: %s", exc)
            return {}

    def fetch_offline(self) -> Dict[str, Any]:
        capture_path = self.config.get("capture_path")
        if not capture_path:
            self.logger.warning("AIS connector missing capture_path configuration")
            return {}

        path = Path(capture_path)
        if not path.exists():
            self.logger.error("AIS capture file does not exist: %s", path)
            return {}

        raw_data = path.read_text(encoding="utf-8", errors="ignore")
        return {"raw_data": raw_data, "status": "replayed"}

