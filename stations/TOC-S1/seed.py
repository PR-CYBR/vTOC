#!/usr/bin/env python
"""Seed maritime telemetry for TOC-S1."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import os
import sys

DEFAULT_DATABASE_URL = "postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s1"
os.environ.setdefault("DATABASE_URL_TOC_S1", DEFAULT_DATABASE_URL)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app import models  # noqa: E402
from app.db import session_scope  # noqa: E402

STATION_SLUG = "toc-s1"


def ensure_station_metadata() -> models.Station:
    with session_scope() as session:
        station = (
            session.query(models.Station)
            .filter(models.Station.slug == STATION_SLUG)
            .one_or_none()
        )
        if station is None:
            station = models.Station(
                slug=STATION_SLUG,
                name="TOC-S1 Coastal Watch",
                description="Littoral radar and AIS aggregation cell",
                timezone="America/Puerto_Rico",
                telemetry_schema="toc_s1",
            )
            session.add(station)
            session.commit()
            session.refresh(station)
        return station


def seed_station_payloads(station: models.Station) -> None:
    with session_scope(STATION_SLUG) as session:
        station_copy = (
            session.query(models.Station)
            .filter(models.Station.id == station.id)
            .one_or_none()
        )
        if station_copy is None:
            station_copy = models.Station(
                id=station.id,
                slug=station.slug,
                name=station.name,
                description=station.description,
                timezone=station.timezone,
                telemetry_schema=station.telemetry_schema,
            )
            session.add(station_copy)
            session.commit()

        source = (
            session.query(models.TelemetrySource)
            .filter(models.TelemetrySource.slug == "s1-littoral-radar")
            .one_or_none()
        )
        if source is None:
            source = models.TelemetrySource(
                name="S1 Littoral Radar",
                slug="s1-littoral-radar",
                source_type="radar",
                description="Surface search radar",
                station_id=station.id,
            )
            session.add(source)
            session.commit()
            session.refresh(source)

        event = models.TelemetryEvent(
            source_id=source.id,
            station_id=station.id,
            event_time=datetime.utcnow() - timedelta(minutes=5),
            latitude=18.201,
            longitude=-66.5,
            payload={"track": "ALPHA", "threat": "observe"},
        )
        session.add(event)
        session.commit()


def main() -> None:
    station = ensure_station_metadata()
    seed_station_payloads(station)
    print("Seeded TOC-S1 telemetry fixtures.")


if __name__ == "__main__":
    main()
