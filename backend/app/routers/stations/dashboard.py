"""Station dashboard endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ... import models, schemas
from ...db import get_db, session_scope

router = APIRouter(prefix="/api/v1/stations", tags=["station-dashboard"])


def _get_station(db: Session, station_slug: str) -> models.Station:
    station = (
        db.query(models.Station)
        .filter(models.Station.slug == station_slug.lower())
        .one_or_none()
    )
    if station is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
    return station


@router.get("/", response_model=List[schemas.StationRead])
def list_stations(db: Session = Depends(get_db)) -> List[models.Station]:
    return db.query(models.Station).order_by(models.Station.slug).all()


@router.get("/{station_slug}", response_model=schemas.StationRead)
def read_station(station_slug: str, db: Session = Depends(get_db)) -> models.Station:
    return _get_station(db, station_slug)


@router.get("/{station_slug}/dashboard", response_model=schemas.StationDashboard)
def station_dashboard(
    station_slug: str,
    db: Session = Depends(get_db),
) -> schemas.StationDashboard:
    station = _get_station(db, station_slug)
    with session_scope(station.slug) as station_session:
        total_events = (
            station_session.query(func.count(models.TelemetryEvent.id))
            .filter(models.TelemetryEvent.station_id == station.id)
            .scalar()
            or 0
        )
        active_sources = (
            station_session.query(func.count(models.TelemetrySource.id))
            .filter(models.TelemetrySource.station_id == station.id)
            .filter(models.TelemetrySource.is_active.is_(True))
            .scalar()
            or 0
        )
        last_event = (
            station_session.query(models.TelemetryEvent)
            .filter(models.TelemetryEvent.station_id == station.id)
            .order_by(models.TelemetryEvent.event_time.desc())
            .limit(1)
            .one_or_none()
        )

    metrics = schemas.StationDashboardMetrics(
        total_events=total_events,
        active_sources=active_sources,
        last_event=last_event,
    )
    return schemas.StationDashboard(station=station, metrics=metrics)
