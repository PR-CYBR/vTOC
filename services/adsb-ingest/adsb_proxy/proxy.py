"""Lightweight proxy around dump1090/readsb JSON output."""
from __future__ import annotations

import asyncio
import copy
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin

import httpx

from .config import Settings

logger = logging.getLogger(__name__)


def _normalise_snapshot(snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not snapshot:
        return {"aircraft": []}
    if "aircraft" not in snapshot or not isinstance(snapshot["aircraft"], list):
        return {"aircraft": []}
    return snapshot


def _aircraft_hash(record: Dict[str, Any]) -> str:
    """Return a stable hash of an aircraft record."""

    # We only care about keys that typically change between updates.
    interesting = {
        key: record.get(key)
        for key in (
            "hex",
            "version",
            "seen",
            "seen_pos",
            "lat",
            "lon",
            "alt_baro",
            "alt_geom",
            "gs",
            "ias",
            "tas",
            "track",
            "baro_rate",
            "geom_rate",
            "nic",
            "rc",
        )
    }
    return json.dumps(interesting, sort_keys=True, separators=(",", ":"))


@dataclass(slots=True)
class HealthStatus:
    status: str
    last_update: Optional[datetime]
    last_push: Optional[datetime]
    error: Optional[str]


class AircraftProxy:
    """Poll aircraft state and proxy it to downstream consumers."""

    def __init__(
        self,
        settings: Settings,
        *,
        backend_client: Optional[httpx.AsyncClient] = None,
        fetch_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.settings = settings
        self._backend_client = backend_client or httpx.AsyncClient(
            base_url=settings.backend_base_url,
            timeout=settings.push_timeout,
        )
        self._fetch_client = fetch_client or httpx.AsyncClient(
            timeout=settings.request_timeout
        )
        self._snapshot: Dict[str, Any] = {"aircraft": []}
        self._hashes: Dict[str, str] = {}
        self._last_update: Optional[datetime] = None
        self._last_push: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._lock = asyncio.Lock()
        self._polling_task: Optional[asyncio.Task[None]] = None
        self._stopping = asyncio.Event()
        endpoint = settings.telemetry_endpoint.lstrip("/")
        self._telemetry_url = urljoin(
            settings.backend_base_url.rstrip("/") + "/", endpoint
        )

    async def start(self) -> None:
        if self._polling_task and not self._polling_task.done():
            return
        self._stopping.clear()
        self._polling_task = asyncio.create_task(self._poll_loop(), name="adsb-poll-loop")

    async def stop(self) -> None:
        self._stopping.set()
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        await self._backend_client.aclose()
        await self._fetch_client.aclose()

    async def get_snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            return copy.deepcopy(self._snapshot)

    async def ingest_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Public helper for injecting a snapshot (primarily for tests)."""
        await self._handle_snapshot(snapshot)

    def health(self) -> HealthStatus:
        now = datetime.now(timezone.utc)
        if self._last_update is None:
            status = "initializing"
        else:
            delta = (now - self._last_update).total_seconds()
            if delta > self.settings.health_ttl_seconds:
                status = "stale"
            else:
                status = "ok"
        return HealthStatus(
            status=status,
            last_update=self._last_update,
            last_push=self._last_push,
            error=self._last_error,
        )

    async def _poll_loop(self) -> None:
        logger.info("Starting ADS-B poll loop with interval %s", self.settings.poll_interval_seconds)
        while not self._stopping.is_set():
            try:
                snapshot = await self._fetch_snapshot()
                if snapshot is not None:
                    await self._handle_snapshot(snapshot)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Unexpected error in poll loop: %s", exc)
                self._last_error = str(exc)
            try:
                await asyncio.wait_for(
                    self._stopping.wait(), timeout=self.settings.poll_interval_seconds
                )
            except asyncio.TimeoutError:
                pass

    async def _fetch_snapshot(self) -> Optional[Dict[str, Any]]:
        if self.settings.readsb_file:
            path = Path(self.settings.readsb_file)
            try:
                snapshot = json.loads(path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                logger.warning("aircraft.json missing at %s", path)
                self._last_error = f"aircraft.json missing at {path}"
                return {"aircraft": []}
            except json.JSONDecodeError as exc:
                logger.error("Invalid aircraft.json: %s", exc)
                self._last_error = f"Invalid aircraft.json: {exc}"
                return {"aircraft": []}
            return snapshot
        if not self.settings.readsb_url:
            return None
        try:
            response = await self._fetch_client.get(self.settings.readsb_url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.warning("Failed to fetch aircraft snapshot: %s", exc)
            self._last_error = str(exc)
            return None

    async def _handle_snapshot(self, snapshot: Dict[str, Any]) -> None:
        snapshot = _normalise_snapshot(snapshot)
        async with self._lock:
            self._snapshot = snapshot
            self._last_update = datetime.now(timezone.utc)
        changed = self._collect_changes(snapshot.get("aircraft", []))
        if changed:
            if await self._push_updates(changed):
                self._last_push = datetime.now(timezone.utc)
                self._last_error = None

    def _collect_changes(
        self, aircraft_list: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        seen_hex: Dict[str, str] = {}
        changed: List[Dict[str, Any]] = []
        for record in aircraft_list:
            hex_id = record.get("hex")
            if not hex_id:
                continue
            record_hash = _aircraft_hash(record)
            seen_hex[hex_id] = record_hash
            if self._hashes.get(hex_id) != record_hash:
                changed.append(record)
        # Drop stale aircraft from cache
        for missing in set(self._hashes) - set(seen_hex):
            del self._hashes[missing]
        for hex_id, record_hash in seen_hex.items():
            self._hashes[hex_id] = record_hash
        return changed

    async def _push_updates(self, aircraft_list: Iterable[Dict[str, Any]]) -> bool:
        success = True
        for record in aircraft_list:
            payload = self._build_event(record)
            if payload is None:
                continue
            try:
                response = await self._backend_client.post(self._telemetry_url, json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("Failed to push telemetry update: %s", exc)
                self._last_error = str(exc)
                success = False
        return success
    def _build_event(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        hex_id = record.get("hex")
        if not hex_id:
            return None
        now = datetime.now(timezone.utc).isoformat()
        event_time = now
        # prefer the ADS-B provided timestamp if present
        seen = record.get("seen")
        if isinstance(seen, (int, float)):
            event_time = (datetime.now(timezone.utc) - timedelta(seconds=seen)).isoformat()
        latitude = record.get("lat")
        longitude = record.get("lon")
        altitude = record.get("alt_baro") or record.get("alt_geom")
        heading = record.get("track")
        speed = record.get("gs") or record.get("tas") or record.get("ias")
        event: Dict[str, Any] = {
            "source_slug": self.settings.telemetry_source_slug,
            "station_id": self.settings.station_id,
            "event_time": event_time,
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "heading": heading,
            "speed": speed,
            "payload": {
                "hex": hex_id,
                "flight": record.get("flight"),
                "squawk": record.get("squawk"),
                "category": record.get("category"),
                "rssi": record.get("rssi"),
                "messages": record.get("messages"),
                "type": record.get("type"),
            },
            "raw_data": json.dumps(record, sort_keys=True),
            "status": "received",
        }
        return event


__all__ = ["AircraftProxy", "HealthStatus"]
