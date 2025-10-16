#!/usr/bin/env python
"""Seed AgentKit telemetry for TOC-S3."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import sys

DEFAULT_DATABASE_URL = (
    os.getenv("SUPABASE_DB_URL_TOC_S3")
    or os.getenv("SUPABASE_DB_URL")
    or os.getenv("DATABASE_URL_TOC_S3")
    or os.getenv("DATABASE_URL")
    or "postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s3"
)
os.environ.setdefault("SUPABASE_DB_URL_TOC_S3", DEFAULT_DATABASE_URL)
os.environ.setdefault("DATABASE_URL_TOC_S3", DEFAULT_DATABASE_URL)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app import models  # noqa: E402
from app.db import session_scope  # noqa: E402

STATION_SLUG = "toc-s3"


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
                name="TOC-S3 Agent Operations",
                description="Agent planning and orchestration",
                timezone="UTC",
                telemetry_schema="toc_s3",
            )
            session.add(station)
            session.commit()
            session.refresh(station)
        return station


def seed_agent_events(station: models.Station) -> None:
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
            .filter(models.TelemetrySource.slug == "s3-agent-bridge")
            .one_or_none()
        )
        if source is None:
            source = models.TelemetrySource(
                name="Agent Operations Bridge",
                slug="s3-agent-bridge",
                source_type="agent",
                description="AgentKit orchestrator",
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
                "agent": "mission_planner",
                "status": "tasking_complete",
                "objective": "Resupply Isla Verde",
            },
        )
        session.add(event)
        session.commit()


def main() -> None:
    station = ensure_station()
    seed_agent_events(station)
    print("Seeded TOC-S3 agent telemetry.")


if __name__ == "__main__":
    main()
