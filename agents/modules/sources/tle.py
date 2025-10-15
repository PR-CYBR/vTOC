from pathlib import Path
from typing import Any, Dict

import requests

from .base import TelemetrySourceConnector


class TLESourceConnector(TelemetrySourceConnector):
    """Connector for satellite TLE data."""

    def fetch_online(self) -> Dict[str, Any]:
        tle_url = self.config.get("tle_url")
        if not tle_url:
            self.logger.warning("TLE connector missing tle_url configuration")
            return {}

        try:
            response = self.session.get(
                tle_url, timeout=self.config.get("timeout", 10)
            )
            response.raise_for_status()
            return {"raw_data": response.text, "status": "received"}
        except requests.RequestException as exc:
            self.logger.error("Failed to fetch TLE data: %s", exc)
            return {}

    def fetch_offline(self) -> Dict[str, Any]:
        tle_file = self.config.get("tle_file")
        if not tle_file:
            self.logger.warning("TLE connector missing tle_file configuration")
            return {}

        path = Path(tle_file)
        if not path.exists():
            self.logger.error("TLE file does not exist: %s", path)
            return {}

        raw_data = path.read_text(encoding="utf-8", errors="ignore")
        return {"raw_data": raw_data, "status": "replayed"}

