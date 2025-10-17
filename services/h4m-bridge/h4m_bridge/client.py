"""HTTP client for posting bridge events."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Dict
from urllib import request, error

LOGGER = logging.getLogger(__name__)


@dataclass
class BridgeClient:
    """Simple HTTP client that posts JSON payloads to the backend."""

    backend_url: str
    timeout: float = 10.0

    def post_event(self, payload: Dict[str, object]) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.backend_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                response.read()  # ensure request completes
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
            LOGGER.error(
                "Backend rejected log event", extra={"status": exc.code, "reason": exc.reason, "body": body}
            )
            raise
        except error.URLError as exc:
            LOGGER.error("Failed to reach backend", extra={"reason": str(exc)})
            raise

