"""Supabase repository abstraction for telemetry and agent audits."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

import httpx
from fastapi import Depends, HTTPException, Request, status

from .. import schemas
from ..config import Settings, get_settings

STATION_HEADER_CANDIDATES = (
    "x-station-id",
    "x-station-slug",
    "x-chatkit-station",
    "x-toc-station",
)


class SupabaseApiError(Exception):
    """Raised when Supabase returns an error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class SupabaseRepository:
    """HTTP based repository wrapper for Supabase PostgREST tables."""

    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        if not settings.is_supabase_configured:
            raise SupabaseApiError(
                status.HTTP_503_SERVICE_UNAVAILABLE, "Supabase is not configured"
            )
        base_url = settings.supabase_url.rstrip("/")
        self._client = client or httpx.Client(
            base_url=f"{base_url}/rest/v1",
            timeout=settings.supabase_timeout_seconds,
        )
        self._schema = settings.supabase_schema
        self._headers: Dict[str, str] = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {settings.supabase_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._station_cache: Dict[str, schemas.StationRead] = {}

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: Any = None,
    ) -> httpx.Response:
        request_headers = {**self._headers}
        if headers:
            request_headers.update(headers)
        request_headers.setdefault("Accept-Profile", self._schema)
        if method.upper() in {"POST", "PUT", "PATCH"}:
            request_headers.setdefault("Content-Profile", self._schema)
        try:
            response = self._client.request(
                method,
                path.lstrip("/"),
                params=params,
                headers=request_headers,
                json=json,
            )
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            raise SupabaseApiError(
                status.HTTP_502_BAD_GATEWAY, "Supabase request failed"
            ) from exc
        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            raise SupabaseApiError(response.status_code, detail)
        return response

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            data = response.json()
        except Exception:  # pragma: no cover - non JSON error
            return response.text or "Supabase request failed"
        if isinstance(data, dict):
            return data.get("message") or data.get("error") or response.text or "Error"
        return response.text or "Error"

    @staticmethod
    def _json(response: httpx.Response) -> Any:
        if not response.content:
            return None
        return response.json()

    @staticmethod
    def _ensure_single(
        response: httpx.Response, *, not_found_message: str = "Record not found"
    ) -> Dict[str, Any]:
        payload = SupabaseRepository._json(response) or []
        if isinstance(payload, list):
            if not payload:
                raise SupabaseApiError(status.HTTP_404_NOT_FOUND, not_found_message)
            return payload[0]
        if isinstance(payload, dict) and payload:
            return payload
        raise SupabaseApiError(status.HTTP_404_NOT_FOUND, not_found_message)

    @staticmethod
    def _parse_count(response: httpx.Response) -> int:
        content_range = response.headers.get("content-range", "0-0/0")
        try:
            _, total = content_range.split("/")
            return int(total)
        except Exception:  # pragma: no cover - defensive parsing
            return 0

    def _count(self, table: str, filters: Dict[str, Any]) -> int:
        params = {"select": "id"}
        params.update(filters)
        response = self._request(
            "GET",
            table,
            params=params,
            headers={"Range": "0-0", "Prefer": "count=exact"},
        )
        return self._parse_count(response)

    # ------------------------------------------------------------------
    # Station helpers
    # ------------------------------------------------------------------
    def list_stations(self) -> List[schemas.StationRead]:
        response = self._request(
            "GET",
            "stations",
            params={"select": "*", "order": "slug.asc"},
        )
        data = self._json(response) or []
        return [schemas.StationRead.model_validate(item) for item in data]

    def get_station(self, station_slug: str) -> schemas.StationRead:
        slug = station_slug.lower()
        if slug in self._station_cache:
            return self._station_cache[slug]
        response = self._request(
            "GET",
            "stations",
            params={"select": "*", "slug": f"eq.{slug}", "limit": 1},
        )
        record = self._ensure_single(response, not_found_message="Station not found")
        station = schemas.StationRead.model_validate(record)
        self._station_cache[slug] = station
        return station

    def station_dashboard(self, station_slug: str) -> schemas.StationDashboard:
        station = self.get_station(station_slug)
        filters = {"station_id": f"eq.{station.id}"}
        total_events = self._count("telemetry_events", filters)
        active_sources = self._count(
            "telemetry_sources", {**filters, "is_active": "eq.true"}
        )
        response = self._request(
            "GET",
            "telemetry_events",
            params={
                "select": "*",
                "station_id": f"eq.{station.id}",
                "order": "event_time.desc",
                "limit": 1,
            },
        )
        payload = self._json(response) or []
        last_event = None
        if payload:
            last_event = schemas.TelemetryEventRead.model_validate(payload[0])
        metrics = schemas.StationDashboardMetrics(
            total_events=total_events,
            active_sources=active_sources,
            last_event=last_event,
        )
        return schemas.StationDashboard(station=station, metrics=metrics)

    def station_task_queue(self, station_slug: str) -> schemas.StationTaskQueue:
        station = self.get_station(station_slug)
        response = self._request(
            "GET",
            "station_assignments",
            params={
                "select": "*,source:telemetry_sources(*)",
                "station_id": f"eq.{station.id}",
                "order": "created_at.desc",
            },
        )
        assignments = self._json(response) or []
        tasks: List[schemas.StationTask] = []
        for assignment in assignments:
            source = assignment.get("source")
            if not source:
                continue
            created_at = assignment.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            updated_at = assignment.get("updated_at")
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            task = schemas.StationTask(
                id=f"{station.slug}:{source.get('slug')}:{assignment.get('id')}",
                title=f"Monitor {source.get('name')}",
                status="active" if assignment.get("is_active") else "paused",
                priority="high" if assignment.get("role") == "primary" else "normal",
                created_at=created_at,
                due_at=updated_at,
                metadata={
                    "role": assignment.get("role"),
                    "source_slug": source.get("slug"),
                    "connection_mode": source.get("connection_mode"),
                },
            )
            tasks.append(task)
        return schemas.StationTaskQueue(station=station, tasks=tasks)

    # ------------------------------------------------------------------
    # Telemetry sources
    # ------------------------------------------------------------------
    def list_telemetry_sources(
        self, station_slug: Optional[str] = None
    ) -> List[schemas.TelemetrySourceRead]:
        params: Dict[str, Any] = {
            "select": "*,station:stations(*)",
            "order": "name.asc",
        }
        if station_slug:
            station = self.get_station(station_slug)
            params["station_id"] = f"eq.{station.id}"
        response = self._request("GET", "telemetry_sources", params=params)
        data = self._json(response) or []
        return [schemas.TelemetrySourceRead.model_validate(item) for item in data]

    def _get_source_by(self, **filters: Any) -> schemas.TelemetrySourceRead:
        params = {"select": "*,station:stations(*)", "limit": 1}
        params.update({key: f"eq.{value}" for key, value in filters.items()})
        response = self._request("GET", "telemetry_sources", params=params)
        record = self._ensure_single(response, not_found_message="Source not found")
        return schemas.TelemetrySourceRead.model_validate(record)

    def get_telemetry_source(self, source_id: int) -> schemas.TelemetrySourceRead:
        return self._get_source_by(id=source_id)

    def get_telemetry_source_by_slug(self, slug: str) -> schemas.TelemetrySourceRead:
        return self._get_source_by(slug=slug.lower())

    def create_telemetry_source(
        self, payload: schemas.TelemetrySourceCreate
    ) -> schemas.TelemetrySourceRead:
        response = self._request(
            "POST",
            "telemetry_sources",
            json=payload.model_dump(exclude_none=True),
            headers={"Prefer": "return=representation"},
        )
        record = self._ensure_single(response)
        return schemas.TelemetrySourceRead.model_validate(record)

    def update_telemetry_source(
        self, source_id: int, payload: schemas.TelemetrySourceUpdate
    ) -> schemas.TelemetrySourceRead:
        data = payload.model_dump(exclude_unset=True)
        response = self._request(
            "PATCH",
            "telemetry_sources",
            params={"id": f"eq.{source_id}"},
            json=data,
            headers={"Prefer": "return=representation"},
        )
        record = self._ensure_single(response, not_found_message="Source not found")
        return schemas.TelemetrySourceRead.model_validate(record)

    def delete_telemetry_source(self, source_id: int) -> None:
        # Ensure the source exists to return a 404 when appropriate
        self.get_telemetry_source(source_id)
        self._request(
            "DELETE",
            "telemetry_sources",
            params={"id": f"eq.{source_id}"},
        )

    # ------------------------------------------------------------------
    # Telemetry events
    # ------------------------------------------------------------------
    def list_telemetry_events(
        self,
        *,
        station_slug: Optional[str] = None,
        limit: int = 100,
    ) -> List[schemas.TelemetryEventWithSource]:
        params: Dict[str, Any] = {
            "select": "*,source:telemetry_sources(*,station:stations(*)),station:stations(*)",
            "order": "event_time.desc",
        }
        if station_slug:
            station = self.get_station(station_slug)
            params["station_id"] = f"eq.{station.id}"
        headers = {"Range": f"0-{max(limit - 1, 0)}"}
        response = self._request(
            "GET",
            "telemetry_events",
            params=params,
            headers=headers,
        )
        data = self._json(response) or []
        return [schemas.TelemetryEventWithSource.model_validate(item) for item in data]

    def get_telemetry_event(self, event_id: int) -> schemas.TelemetryEventWithSource:
        response = self._request(
            "GET",
            "telemetry_events",
            params={
                "select": "*,source:telemetry_sources(*,station:stations(*)),station:stations(*)",
                "id": f"eq.{event_id}",
                "limit": 1,
            },
        )
        record = self._ensure_single(response, not_found_message="Event not found")
        return schemas.TelemetryEventWithSource.model_validate(record)

    def create_telemetry_event(
        self, payload: schemas.TelemetryEventCreate
    ) -> schemas.TelemetryEventRead:
        source: Optional[schemas.TelemetrySourceRead] = None
        if payload.source_id is not None:
            source = self.get_telemetry_source(payload.source_id)
        elif payload.source_slug:
            try:
                source = self.get_telemetry_source_by_slug(payload.source_slug)
            except SupabaseApiError as exc:
                if exc.status_code != status.HTTP_404_NOT_FOUND:
                    raise
                if payload.source_name:
                    source = self.create_telemetry_source(
                        schemas.TelemetrySourceCreate(
                            name=payload.source_name,
                            slug=payload.source_slug,
                            source_type="external",
                            description="Created via telemetry ingestion",
                            station_id=payload.station_id,
                        )
                    )
                else:
                    raise SupabaseApiError(
                        status.HTTP_400_BAD_REQUEST, "Unknown source"
                    ) from exc
        if source is None:
            raise SupabaseApiError(status.HTTP_400_BAD_REQUEST, "Unknown source")

        data = payload.model_dump(
            exclude={"source_id", "source_slug", "source_name"},
            exclude_none=True,
        )
        data["source_id"] = source.id
        if source.station_id and "station_id" not in data:
            data["station_id"] = source.station_id
        response = self._request(
            "POST",
            "telemetry_events",
            json=data,
            headers={"Prefer": "return=representation"},
        )
        record = self._ensure_single(response)
        return schemas.TelemetryEventRead.model_validate(record)

    def update_telemetry_event(
        self, event_id: int, payload: schemas.TelemetryEventUpdate
    ) -> schemas.TelemetryEventRead:
        data = payload.model_dump(exclude_unset=True)
        response = self._request(
            "PATCH",
            "telemetry_events",
            params={"id": f"eq.{event_id}"},
            json=data,
            headers={"Prefer": "return=representation"},
        )
        record = self._ensure_single(response, not_found_message="Event not found")
        return schemas.TelemetryEventRead.model_validate(record)

    def delete_telemetry_event(self, event_id: int) -> None:
        # Ensure existence
        self.get_telemetry_event(event_id)
        self._request(
            "DELETE",
            "telemetry_events",
            params={"id": f"eq.{event_id}"},
        )

    # ------------------------------------------------------------------
    # Agent action audits
    # ------------------------------------------------------------------
    def list_agent_action_audits(
        self, limit: int = 100
    ) -> List[schemas.AgentActionAuditRead]:
        response = self._request(
            "GET",
            "agent_action_audits",
            params={"select": "*", "order": "created_at.desc"},
            headers={"Range": f"0-{max(limit - 1, 0)}"},
        )
        data = self._json(response) or []
        return [schemas.AgentActionAuditRead.model_validate(item) for item in data]

    def get_agent_action_audit_by_action_id(
        self, action_id: str
    ) -> Optional[schemas.AgentActionAuditRead]:
        response = self._request(
            "GET",
            "agent_action_audits",
            params={
                "select": "*",
                "action_id": f"eq.{action_id}",
                "limit": 1,
            },
        )
        payload = self._json(response) or []
        if not payload:
            return None
        return schemas.AgentActionAuditRead.model_validate(payload[0])

    def create_agent_action_audit(
        self, payload: schemas.AgentActionAuditCreate
    ) -> schemas.AgentActionAuditRead:
        response = self._request(
            "POST",
            "agent_action_audits",
            json=payload.model_dump(exclude_none=True),
            headers={"Prefer": "return=representation"},
        )
        record = self._ensure_single(response)
        return schemas.AgentActionAuditRead.model_validate(record)

    def update_agent_action_audit(
        self, audit_id: int, payload: schemas.AgentActionAuditUpdate
    ) -> schemas.AgentActionAuditRead:
        data = payload.model_dump(exclude_unset=True)
        response = self._request(
            "PATCH",
            "agent_action_audits",
            params={"id": f"eq.{audit_id}"},
            json=data,
            headers={"Prefer": "return=representation"},
        )
        record = self._ensure_single(response, not_found_message="Audit not found")
        return schemas.AgentActionAuditRead.model_validate(record)


def resolve_station_slug(request: Request) -> Optional[str]:
    """Infer the station slug from common headers."""
    for header in STATION_HEADER_CANDIDATES:
        value = request.headers.get(header)
        if not value:
            continue
        slug = value.replace("_", "-").lower()
        if slug:
            return slug
    return None


def get_station_context(request: Request) -> Optional[str]:
    return resolve_station_slug(request)


def get_supabase_repository(
    settings: Settings = Depends(get_settings),
) -> Generator[SupabaseRepository, None, None]:
    try:
        repository = SupabaseRepository(settings=settings)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    try:
        yield repository
    finally:
        repository.close()


__all__ = [
    "SupabaseApiError",
    "SupabaseRepository",
    "get_station_context",
    "get_supabase_repository",
    "resolve_station_slug",
]
