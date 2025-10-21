"""Tests for the timeline summary AgentKit playbook."""
from __future__ import annotations

from datetime import datetime, timezone

from agents.playbooks.timeline_summary import TimelineSummaryPlaybook


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class DummyClient:
    def __init__(self, expected_path: str, payload: dict) -> None:
        self.expected_path = expected_path
        self.payload = payload
        self.requested_paths: list[str] = []

    def __enter__(self) -> "DummyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, path: str) -> DummyResponse:
        self.requested_paths.append(path)
        assert path == self.expected_path
        return DummyResponse(self.payload)


def test_timeline_summary_empty_response() -> None:
    """Gracefully handles timelines with no events."""

    payload = {"timeline": []}

    def client_factory() -> DummyClient:
        return DummyClient("/api/v1/stations/test-station/timeline", payload)

    playbook = TimelineSummaryPlaybook(
        station_slug="test-station",
        backend_base_url="https://backend.example",
        station_token="secret-token",
        client_factory=client_factory,
    )
    result = playbook.run()

    assert result.entries == []
    assert "No mission timeline activity" in result.summary
    assert "test-station" in result.summary


def test_timeline_summary_with_events() -> None:
    """Summaries include the event metadata returned by the backend."""

    occurred_at = "2024-03-10T15:45:00Z"
    payload = {
        "timeline": [
            {
                "occurred_at": occurred_at,
                "summary": "Mission launched",
                "details": "Alpha team airborne",
                "actor": "Ops Console",
            },
            {
                "timestamp": datetime(2024, 3, 10, 15, 30, tzinfo=timezone.utc).isoformat(),
                "message": "Refuelling window closed",
                "notes": "Winds exceeding limits",
                "user": "Weather Watch",
            },
        ]
    }

    def client_factory() -> DummyClient:
        return DummyClient("/api/v1/stations/test-station/timeline", payload)

    playbook = TimelineSummaryPlaybook(
        station_slug="test-station",
        backend_base_url="https://backend.example",
        station_token="secret-token",
        client_factory=client_factory,
        limit=2,
    )
    result = playbook.run()

    assert len(result.entries) == 2
    titles = [entry.title for entry in result.entries]
    assert "Mission launched" in titles
    assert "Refuelling window closed" in titles

    summary_lines = result.summary.splitlines()
    assert summary_lines[0].startswith("Latest mission timeline")
    assert any("Alpha team airborne" in line for line in summary_lines)
    assert any("by Ops Console" in line for line in summary_lines)
