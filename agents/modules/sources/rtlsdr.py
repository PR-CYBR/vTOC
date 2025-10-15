from pathlib import Path
from typing import Any, Dict

from .base import TelemetrySourceConnector


class RTLSDRSourceConnector(TelemetrySourceConnector):
    """Connector for RTL-SDR radio captures."""

    def fetch_online(self) -> Dict[str, Any]:
        stream_url = self.config.get("stream_url")
        if not stream_url:
            self.logger.warning("RTL-SDR connector missing stream_url configuration")
            return {}

        # Real-time demodulation is hardware specific. Here we just report availability.
        self.logger.info("Monitoring RTL-SDR stream at %s", stream_url)
        return {"payload": {"stream_url": stream_url}, "status": "listening"}

    def fetch_offline(self) -> Dict[str, Any]:
        iq_file = self.config.get("iq_recording")
        if not iq_file:
            self.logger.warning("RTL-SDR connector missing iq_recording configuration")
            return {}

        path = Path(iq_file)
        if not path.exists():
            self.logger.error("RTL-SDR IQ recording does not exist: %s", path)
            return {}

        self.logger.info("Replaying RTL-SDR IQ capture from %s", path)
        return {"payload": {"iq_file": str(path)}, "status": "replayed"}

