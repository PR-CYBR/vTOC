import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest
from adsb_proxy.config import Settings
from adsb_proxy.proxy import AircraftProxy


@pytest.fixture()
def sample_snapshot() -> dict:
    path = Path(__file__).parent / "data" / "sample_aircraft.json"
    return json.loads(path.read_text(encoding="utf-8"))


async def _run_ingest_snapshot_pushes_unique_updates(sample_snapshot):
    events = []

    async def handler(request: httpx.Request) -> httpx.Response:
        events.append(json.loads(request.content))
        return httpx.Response(201, json={"status": "ok"})

    transport = httpx.MockTransport(handler)
    backend_client = httpx.AsyncClient(transport=transport, base_url="http://backend")
    settings = Settings(
        backend_base_url="http://backend",
        telemetry_endpoint="/api/v1/telemetry/events",
        telemetry_source_slug="adsb-test",
        station_id=7,
        poll_interval_seconds=0.1,
        request_timeout=1.0,
        push_timeout=1.0,
        health_ttl_seconds=10.0,
        readsb_url=None,
    )
    proxy = AircraftProxy(settings, backend_client=backend_client)

    await proxy.ingest_snapshot(sample_snapshot)
    assert len(events) == 2

    # Re-ingesting identical data should not trigger extra events.
    await proxy.ingest_snapshot(sample_snapshot)
    assert len(events) == 2

    mutated = copy.deepcopy(sample_snapshot)
    mutated["aircraft"][0]["gs"] = 450.0

    await proxy.ingest_snapshot(mutated)
    assert len(events) == 3
    assert events[-1]["payload"]["hex"] == "abc123"

    health = proxy.health()
    assert health.status in {"ok", "initializing"}
    assert health.last_push is not None

    await proxy.stop()


def test_ingest_snapshot_pushes_unique_updates(sample_snapshot):
    asyncio.run(_run_ingest_snapshot_pushes_unique_updates(sample_snapshot))


async def _run_snapshot_without_aircraft_is_handled():
    events = []

    async def handler(request: httpx.Request) -> httpx.Response:
        events.append(json.loads(request.content))
        return httpx.Response(201, json={"status": "ok"})

    transport = httpx.MockTransport(handler)
    backend_client = httpx.AsyncClient(transport=transport, base_url="http://backend")
    settings = Settings(
        backend_base_url="http://backend",
        telemetry_source_slug="adsb-test",
        poll_interval_seconds=0.1,
        request_timeout=1.0,
        push_timeout=1.0,
        health_ttl_seconds=10.0,
        readsb_url=None,
    )
    proxy = AircraftProxy(settings, backend_client=backend_client)

    await proxy.ingest_snapshot({})
    assert len(events) == 0
    snapshot = await proxy.get_snapshot()
    assert snapshot["aircraft"] == []

    await proxy.stop()


def test_snapshot_without_aircraft_is_handled():
    asyncio.run(_run_snapshot_without_aircraft_is_handled())
