from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import schemas
from backend.app.services.supabase import get_supabase_repository


class DummySupabaseRepository:
    def __init__(self) -> None:
        self.returned_stations: list[str] = []

    def get_station(self, station_slug: str) -> schemas.StationRead:
        self.returned_stations.append(station_slug)
        now = datetime.utcnow()
        return schemas.StationRead(
            id=1,
            slug=station_slug,
            name="Test Station",
            description="Testing station",
            timezone="UTC",
            telemetry_schema="test_schema",
            created_at=now,
            updated_at=now,
        )


@pytest.fixture()
def client() -> TestClient:
    test_client = TestClient(app)
    repo = DummySupabaseRepository()
    app.dependency_overrides[get_supabase_repository] = lambda: repo
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_supabase_repository, None)
        test_client.close()


def test_agentkit_catalog_includes_mission_timeline(client: TestClient) -> None:
    response = client.get("/api/v1/stations/demo/agentkit/actions")
    assert response.status_code == 200
    payload = response.json()
    action_names = {action["name"] for action in payload["actions"]}
    assert "mission_timeline" in action_names

    timeline_action = next(
        action for action in payload["actions"] if action["name"] == "mission_timeline"
    )
    assert timeline_action["method"] == "GET"
    assert timeline_action["endpoint"].endswith("/api/v1/stations/demo/mission-timeline")

    metadata = timeline_action["metadata"]
    assert metadata["path_params"]["station_slug"]["required"] is True
    assert metadata["query"]["limit"]["default"] == 50
    assert "Timeline entries ordered" in metadata["response"]["description"]
