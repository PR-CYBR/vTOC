#!/usr/bin/env python
"""Seed strategic telemetry for TOC-S4."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import sys

DEFAULT_DATABASE_URL = (
    os.getenv("SUPABASE_DB_URL_TOC_S4")
    or os.getenv("SUPABASE_DB_URL")
    or os.getenv("DATABASE_URL_TOC_S4")
    or os.getenv("DATABASE_URL")
    or "postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s4"
)
os.environ.setdefault("SUPABASE_DB_URL_TOC_S4", DEFAULT_DATABASE_URL)
os.environ.setdefault("DATABASE_URL_TOC_S4", DEFAULT_DATABASE_URL)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app import models  # noqa: E402
from app.db import session_scope  # noqa: E402

STATION_SLUG = "toc-s4"


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
                name="TOC-S4 Strategic Hub",
                description="Command oversight and analytics",
                timezone="UTC",
                telemetry_schema="toc_s4",
            )
            session.add(station)
            session.commit()
            session.refresh(station)
        return station


def seed_rollups(station: models.Station) -> None:
    with session_scope(STATION_SLUG) as session:
        if (
            session.query(models.Station)
            .filter(models.Station.id == station.id)
            .one_or_none()
            is None
        ):
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
            .filter(models.TelemetrySource.slug == "s4-rollup-engine")
            .one_or_none()
        )
        if source is None:
            source = models.TelemetrySource(
                name="Rollup Engine",
                slug="s4-rollup-engine",
                source_type="analytics",
                description="Aggregated command telemetry",
                station_id=station.id,
            )
            session.add(source)
            session.commit()
            session.refresh(source)

        event = models.TelemetryEvent(
            source_id=source.id,
            station_id=station.id,
            event_time=datetime.utcnow(),
            payload={
                "summary": {
                    "toc-s1": "GREEN",
                    "toc-s2": "AMBER",
                    "toc-s3": "GREEN",
                }
            },
        )
        session.add(event)
        session.commit()


def main() -> None:
    station = ensure_station()
    seed_rollups(station)
    print("Seeded TOC-S4 strategic telemetry.")


if __name__ == "__main__":
    main()
