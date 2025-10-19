"""Mission timeline summary playbook for AgentKit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional, Sequence
import os


DEFAULT_BACKEND_BASE_URL = "http://localhost:8080"
DEFAULT_TIMEOUT_SECONDS = 15.0


class TimelineSummaryError(RuntimeError):
    """Raised when the timeline summary playbook fails."""


@dataclass(slots=True)
class TimelineEntry:
    """Normalized representation of a mission timeline event."""

    timestamp: datetime
    title: str
    details: Optional[str] = None
    actor: Optional[str] = None

    @property
    def rendered_timestamp(self) -> str:
        return self.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%MZ")


@dataclass(slots=True)
class TimelineSummaryResult:
    """Result payload produced by the playbook."""

    summary: str
    entries: List[TimelineEntry]
    raw_payload: Any


class TimelineSummaryPlaybook:
    """Fetch the station mission timeline and produce a ChatKit friendly summary."""

    def __init__(
        self,
        *,
        station_slug: Optional[str] = None,
        backend_base_url: Optional[str] = None,
        station_token: Optional[str] = None,
        limit: int = 5,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client_factory: Optional[Callable[[], Any]] = None,
        transport: Any | None = None,
    ) -> None:
        self.station_slug = station_slug or os.getenv("STATION_SLUG") or os.getenv("POSTGRES_STATION_ROLE")
        if not self.station_slug:
            raise TimelineSummaryError("Station slug is required to fetch the mission timeline")

        self.backend_base_url = backend_base_url or os.getenv("BACKEND_BASE_URL") or DEFAULT_BACKEND_BASE_URL
        self.station_token = station_token or os.getenv("STATION_API_TOKEN") or os.getenv("AGENTKIT_STATION_TOKEN")
        self.limit = max(1, int(limit))
        self.timeout_seconds = float(timeout_seconds)
        self._client_factory = client_factory
        self._transport = transport

    # Public API ---------------------------------------------------------
    def run(self) -> TimelineSummaryResult:
        """Execute the playbook and return a formatted summary."""

        entries_raw = self._fetch_timeline()
        entries = self._normalize_entries(entries_raw)
        summary = self._compose_summary(entries)
        return TimelineSummaryResult(summary=summary, entries=entries, raw_payload=entries_raw)

    # Internal helpers ---------------------------------------------------
    def _create_client(self) -> Any:
        if self._client_factory is not None:
            return self._client_factory()

        httpx = self._get_httpx_module()
        if httpx is None:  # pragma: no cover - dependency missing at runtime
            raise TimelineSummaryError("httpx is required to fetch the mission timeline")

        headers = {"Accept": "application/json"}
        if self.station_token:
            headers["Authorization"] = f"Bearer {self.station_token}"
        return httpx.Client(
            base_url=self.backend_base_url,
            timeout=self.timeout_seconds,
            headers=headers,
            transport=self._transport,
        )

    def _fetch_timeline(self) -> Any:
        try:
            with self._create_client() as client:
                response = client.get(f"/api/v1/stations/{self.station_slug}/timeline")
                response.raise_for_status()
                return response.json()
        except Exception as exc:  # pragma: no cover - network error path
            httpx = self._get_httpx_module()
            if httpx and isinstance(exc, httpx.HTTPStatusError):
                raise TimelineSummaryError(
                    f"Backend rejected timeline request: {exc.response.status_code}"
                ) from exc
            if httpx and isinstance(exc, httpx.HTTPError):
                raise TimelineSummaryError("Unable to reach backend timeline endpoint") from exc
            raise

    def _normalize_entries(self, payload: Any) -> List[TimelineEntry]:
        items = self._extract_items(payload)
        entries: List[TimelineEntry] = []
        for item in items[: self.limit]:
            if not isinstance(item, dict):
                continue
            timestamp = self._parse_timestamp(
                item.get("occurred_at")
                or item.get("timestamp")
                or item.get("event_time")
                or item.get("created_at")
            )
            if timestamp is None:
                timestamp = datetime.now(tz=timezone.utc)
            title = self._coalesce(
                item.get("summary"),
                item.get("title"),
                item.get("message"),
                item.get("description"),
            )
            if not title:
                title = "Timeline event"
            details = self._coalesce(
                item.get("details"),
                item.get("notes"),
                item.get("context"),
                item.get("metadata"),
            )
            if isinstance(details, dict):
                details = ", ".join(f"{key}: {value}" for key, value in details.items())
            actor = self._coalesce(item.get("actor"), item.get("user"), item.get("author"))
            entries.append(TimelineEntry(timestamp=timestamp, title=str(title), details=self._string_or_none(details), actor=self._string_or_none(actor)))
        entries.sort(key=lambda entry: entry.timestamp, reverse=True)
        return entries

    def _compose_summary(self, entries: Sequence[TimelineEntry]) -> str:
        if not entries:
            return (
                f"No mission timeline activity found for station `{self.station_slug}`. "
                "ChatKit will be updated when new events arrive."
            )
        lines = [
            f"Latest mission timeline for `{self.station_slug}` (showing {len(entries)} events):",
        ]
        for entry in entries:
            line = f"- {entry.rendered_timestamp} – {entry.title}"
            if entry.actor:
                line += f" (by {entry.actor})"
            if entry.details:
                line += f": {entry.details}"
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _get_httpx_module() -> Any | None:
        try:
            import httpx  # type: ignore
        except ModuleNotFoundError:
            return None
        return httpx

    @staticmethod
    def _extract_items(payload: Any) -> List[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("timeline", "items", "events", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            return [payload]
        return []

    @staticmethod
    def _coalesce(*values: Any) -> Optional[str]:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
            if value is not None and not isinstance(value, (list, dict)):
                return str(value)
        return None

    @staticmethod
    def _string_or_none(value: Any) -> Optional[str]:
        if isinstance(value, str):
            return value.strip() or None
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if isinstance(value, str) and value.strip():
            normalized = value.strip().replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                pass
        return None


__all__ = [
    "TimelineSummaryPlaybook",
    "TimelineSummaryResult",
    "TimelineEntry",
    "TimelineSummaryError",
]
