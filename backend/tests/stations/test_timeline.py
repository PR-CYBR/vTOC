from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from backend.app import schemas
from backend.app.config import Settings
from backend.app.main import app
from backend.app.services.supabase import (
    SupabaseRepository,
    get_supabase_repository,
)


class DummyClient:
    def request(self, *args: Any, **kwargs: Any) -> None:
        raise AssertionError("HTTP calls should not be made in timeline tests")

    def close(self) -> None:
        pass


class FakeTimelineRepository(SupabaseRepository):
    def __init__(
        self,
        settings: Settings,
        telemetry_records: List[Dict[str, Any]],
        audit_records: List[Dict[str, Any]],
    ) -> None:
        super().__init__(settings=settings, client=DummyClient())
        now = datetime.now(timezone.utc)
        self._station = schemas.StationRead(
            id=1,
            name="Test Station",
            slug="test-station",
            description="Station used for timeline tests",
            timezone="UTC",
            telemetry_schema=None,
            created_at=now,
            updated_at=now,
        )
        self._telemetry_all = telemetry_records
        self._audits_all = audit_records

    def close(self) -> None:  # pragma: no cover - no external resources
        pass

    def get_station(self, station_slug: str) -> schemas.StationRead:  # type: ignore[override]
        return self._station

    def _fetch_station_timeline_telemetry_records(  # type: ignore[override]
        self, station_id: int, limit: int
    ) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        return self._telemetry_all[:limit]

    def _fetch_station_timeline_agent_audit_records(  # type: ignore[override]
        self, station_id: int, limit: int
    ) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        return self._audits_all[:limit]

    def _count(self, table: str, filters: Dict[str, Any]) -> int:  # type: ignore[override]
        if table == "telemetry_events":
            return len(self._telemetry_all)
        if table == "agent_action_audits":
            return len(self._audits_all)
        return 0


@pytest.fixture()
def timeline_repo() -> FakeTimelineRepository:
    base = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    telemetry_records = [
        {
            "id": 101,
            "event_time": (base - timedelta(minutes=5)).isoformat(),
            "received_at": (base - timedelta(minutes=5)).isoformat(),
            "created_at": (base - timedelta(minutes=5)).isoformat(),
            "status": "received",
            "payload": {"value": 101},
            "source": {"slug": "primary-radar", "name": "Primary Radar"},
        },
        {
            "id": 102,
            "event_time": None,
            "received_at": (base - timedelta(minutes=1)).isoformat(),
            "created_at": (base - timedelta(minutes=1)).isoformat(),
            "status": "received",
            "payload": {"value": 102},
            "source": {"slug": "primary-radar", "name": "Primary Radar"},
        },
        {
            "id": 103,
            "event_time": (base - timedelta(minutes=9)).isoformat(),
            "received_at": (base - timedelta(minutes=9)).isoformat(),
            "created_at": (base - timedelta(minutes=9)).isoformat(),
            "status": "received",
            "payload": {"value": 103},
            "source": {"slug": "primary-radar", "name": "Primary Radar"},
        },
    ]
    audit_records = [
        {
            "id": 201,
            "action_id": "audit-1",
            "tool_name": "ping",
            "status": "succeeded",
            "response_payload": {"ok": True},
            "error_message": None,
            "completed_at": (base - timedelta(minutes=3)).isoformat(),
            "updated_at": (base - timedelta(minutes=3)).isoformat(),
            "created_at": (base - timedelta(minutes=4)).isoformat(),
        },
        {
            "id": 202,
            "action_id": "audit-2",
            "tool_name": "ping",
            "status": "failed",
            "response_payload": None,
            "error_message": "timeout",
            "completed_at": None,
            "updated_at": (base - timedelta(minutes=6)).isoformat(),
            "created_at": (base - timedelta(minutes=7)).isoformat(),
        },
    ]
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role",
    )
    return FakeTimelineRepository(settings, telemetry_records, audit_records)


@pytest.fixture()
def client(timeline_repo: FakeTimelineRepository) -> TestClient:
    test_client = TestClient(app)
    app.dependency_overrides[get_supabase_repository] = lambda: timeline_repo
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_supabase_repository, None)
        test_client.close()


def test_station_timeline_orders_entries_desc(client: TestClient) -> None:
    response = client.get("/api/v1/stations/test-station/timeline")
    assert response.status_code == 200
    payload = response.json()

    assert payload["total"] == 5
    occurred_at_values = [item["occurred_at"] for item in payload["items"]]
    assert occurred_at_values == sorted(occurred_at_values, reverse=True)

    first_entry = payload["items"][0]
    assert first_entry["entry_type"] == "telemetry_event"
    assert first_entry["event_id"] == 102

    second_entry = payload["items"][1]
    assert second_entry["entry_type"] == "agent_action_audit"
    assert second_entry["audit_id"] == 201


def test_station_timeline_supports_pagination(client: TestClient) -> None:
    response = client.get(
        "/api/v1/stations/test-station/timeline",
        params={"limit": 2, "offset": 1},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["limit"] == 2
    assert payload["offset"] == 1
    assert payload["total"] == 5
    assert len(payload["items"]) == 2

    # Entries should represent the 2nd and 3rd most recent timeline items
    entry_types = [item["entry_type"] for item in payload["items"]]
    assert entry_types == ["agent_action_audit", "telemetry_event"]
    assert payload["items"][0]["audit_id"] == 201
    assert payload["items"][1]["event_id"] == 101
