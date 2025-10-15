from pathlib import Path
from typing import Any, Dict

from .base import TelemetrySourceConnector


class GPSSourceConnector(TelemetrySourceConnector):
    """Connector for GPS receivers and track logs."""

    def fetch_online(self) -> Dict[str, Any]:
        ntrip_endpoint = self.config.get("ntrip_endpoint")
        if ntrip_endpoint:
            self.logger.info("Connecting to NTRIP caster at %s", ntrip_endpoint)
            return {"payload": {"ntrip_endpoint": ntrip_endpoint}, "status": "listening"}

        self.logger.warning("GPS connector has no online source configured")
        return {}

    def fetch_offline(self) -> Dict[str, Any]:
        gpx_file = self.config.get("gpx_file")
        nmea_log = self.config.get("nmea_log")

        path_value = gpx_file or nmea_log
        if not path_value:
            self.logger.warning("GPS connector missing gpx_file or nmea_log configuration")
            return {}

        path = Path(path_value)
        if not path.exists():
            self.logger.error("GPS log does not exist: %s", path)
            return {}

        raw_data = path.read_text(encoding="utf-8", errors="ignore")
        return {"raw_data": raw_data, "status": "replayed"}

