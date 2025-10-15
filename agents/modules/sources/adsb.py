from pathlib import Path
from typing import Any, Dict

import requests

from .base import TelemetrySourceConnector


class ADSBSourceConnector(TelemetrySourceConnector):
    """Connector for ADS-B aircraft telemetry feeds."""

    def fetch_online(self) -> Dict[str, Any]:
        api_url = self.config.get("api_url")
        if not api_url:
            self.logger.warning("ADSB connector missing api_url configuration")
            return {}

        params = self.config.get("params", {})
        try:
            response = self.session.get(
                api_url, params=params, timeout=self.config.get("timeout", 10)
            )
            response.raise_for_status()
            data = response.json()
            return {"payload": data, "status": "received"}
        except requests.RequestException as exc:
            self.logger.error("Failed to fetch ADSB data: %s", exc)
            return {}

    def fetch_offline(self) -> Dict[str, Any]:
        log_path = self.config.get("log_path")
        if not log_path:
            self.logger.warning("ADSB connector missing log_path configuration")
            return {}

        path = Path(log_path)
        if not path.exists():
            self.logger.error("ADSB log file does not exist: %s", path)
            return {}

        raw_data = path.read_text(encoding="utf-8", errors="ignore")
        return {"raw_data": raw_data, "status": "replayed"}

