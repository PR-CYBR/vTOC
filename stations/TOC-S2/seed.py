#!/usr/bin/env python
"""Seed airborne telemetry for TOC-S2."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import os
import sys

DEFAULT_DATABASE_URL = (
    os.getenv("SUPABASE_DB_URL_TOC_S2")
    or os.getenv("SUPABASE_DB_URL")
    or os.getenv("DATABASE_URL_TOC_S2")
    or os.getenv("DATABASE_URL")
    or "postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s2"
)
os.environ.setdefault("SUPABASE_DB_URL_TOC_S2", DEFAULT_DATABASE_URL)
os.environ.setdefault("DATABASE_URL_TOC_S2", DEFAULT_DATABASE_URL)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app import models  # noqa: E402
from app.db import session_scope  # noqa: E402

STATION_SLUG = "toc-s2"


def ensure_station() -> models.Station:
    with session_scope() as session:
        station = (
            session.query(models.Station)
            .filter(models.Station.slug == STATION_SLUG)
            .one_or_none()
        )
        if station is None:
            station = models.Station(
                slug=STATION_SLUG,
                name="TOC-S2 Air Tasking",
                description="Airborne ISR tasking cell",
                timezone="UTC",
                telemetry_schema="toc_s2",
            )
            session.add(station)
            session.commit()
            session.refresh(station)
        return station


def seed_airframe(station: models.Station) -> None:
    with session_scope(STATION_SLUG) as session:
        station_copy = (
            session.query(models.Station)
            .filter(models.Station.id == station.id)
            .one_or_none()
        )
        if station_copy is None:
            session.add(
                models.Station(
                    id=station.id,
                    slug=station.slug,
                    name=station.name,
                    description=station.description,
                    timezone=station.timezone,
                    telemetry_schema=station.telemetry_schema,
                )
            )
            session.commit()

        source = (
            session.query(models.TelemetrySource)
            .filter(models.TelemetrySource.slug == "s2-rq4-global-hawk")
            .one_or_none()
        )
        if source is None:
            source = models.TelemetrySource(
                name="RQ-4 Global Hawk",
                slug="s2-rq4-global-hawk",
                source_type="uav",
                description="High altitude ISR platform",
                station_id=station.id,
            )
            session.add(source)
            session.commit()
            session.refresh(source)

        event = models.TelemetryEvent(
            source_id=source.id,
            station_id=station.id,
            event_time=datetime.utcnow() - timedelta(minutes=2),
            latitude=18.5,
            longitude=-65.9,
            altitude=45000,
            speed=360,
            payload={"mission": "SCARLET", "sensor": "EO/IR"},
        )
        session.add(event)
        session.commit()


def main() -> None:
    station = ensure_station()
    seed_airframe(station)
    print("Seeded TOC-S2 airborne telemetry.")


if __name__ == "__main__":
    main()
