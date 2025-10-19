"""Tests for station header resolution helpers."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import pytest

from backend.app.utils import stations


class DummyRequest:
    def __init__(self, headers: Dict[str, str]) -> None:
        self.headers = headers


def test_resolve_station_slug_normalises_and_filters_known_slugs() -> None:
    headers = {"x-station-id": "Station_ONE"}
    result = stations.resolve_station_slug(headers, {"station-one", "station-two"})
    assert result == "station-one"


def test_resolve_station_slug_returns_none_for_unknown_when_knowns_provided() -> None:
    headers = {"x-station-id": "unknown"}
    result = stations.resolve_station_slug(headers, {"station-one"})
    assert result is None


def test_resolve_station_slug_allows_unknown_when_no_knowns() -> None:
    headers = {"x-station-slug": "Station_THREE"}
    result = stations.resolve_station_slug(headers, None)
    assert result == "station-three"


def test_supabase_resolve_station_slug_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    supabase = importlib.import_module("backend.app.services.supabase")
    request = DummyRequest({"x-station-id": "Station"})
    sentinel = object()

    def fake(headers, known_slugs):  # type: ignore[no-untyped-def]
        assert headers is request.headers
        assert known_slugs is None
        return sentinel

    monkeypatch.setattr(
        supabase,
        "_resolve_station_slug_from_headers",
        fake,
    )

    assert supabase.resolve_station_slug(request) is sentinel


def test_db_resolve_station_slug_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    db = importlib.import_module("backend.app.db")
    db = importlib.reload(db)
    request = DummyRequest({"x-station-slug": "Station"})
    sentinel = object()

    def fake(headers, known_slugs):  # type: ignore[no-untyped-def]
        assert headers is request.headers
        assert list(known_slugs) == list(db.SESSION_FACTORY_BY_STATION.keys())
        return sentinel

    monkeypatch.setattr(
        db,
        "_resolve_station_slug_from_headers",
        fake,
    )

    assert db._resolve_station_slug(request) is sentinel
