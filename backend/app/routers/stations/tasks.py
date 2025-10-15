"""Station task queues."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from ... import models, schemas
from ...db import get_db
from .dashboard import _get_station

router = APIRouter(prefix="/api/v1/stations", tags=["station-tasks"])


@router.get("/{station_slug}/tasks", response_model=schemas.StationTaskQueue)
def station_task_queue(station_slug: str, db: Session = Depends(get_db)) -> schemas.StationTaskQueue:
    station = _get_station(db, station_slug)
    assignments = (
        db.query(models.StationAssignment)
        .options(selectinload(models.StationAssignment.source))
        .filter(models.StationAssignment.station_id == station.id)
        .order_by(models.StationAssignment.created_at.desc())
        .all()
    )

    tasks = []
    for assignment in assignments:
        source = assignment.source
        if source is None:
            continue
        tasks.append(
            schemas.StationTask(
                id=f"{station.slug}:{source.slug}:{assignment.id}",
                title=f"Monitor {source.name}",
                status="active" if assignment.is_active else "paused",
                priority="high" if assignment.role == "primary" else "normal",
                created_at=assignment.created_at,
                due_at=assignment.updated_at,
                metadata={
                    "role": assignment.role,
                    "source_slug": source.slug,
                    "connection_mode": source.connection_mode,
                },
            )
        )

    return schemas.StationTaskQueue(station=station, tasks=tasks)
