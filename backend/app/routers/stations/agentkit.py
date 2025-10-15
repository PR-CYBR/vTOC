"""Station AgentKit affordances."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ... import schemas
from ...db import get_db
from .dashboard import _get_station

router = APIRouter(prefix="/api/v1/stations", tags=["station-agentkit"])


@router.get(
    "/{station_slug}/agentkit/actions",
    response_model=schemas.StationAgentCatalog,
)
def station_agent_actions(
    station_slug: str, db: Session = Depends(get_db)
) -> schemas.StationAgentCatalog:
    station = _get_station(db, station_slug)
    actions: List[schemas.AgentAction] = [
        schemas.AgentAction(
            name="ingest_telemetry",
            description="Ingest telemetry payloads for the station context.",
            endpoint=f"/api/v1/telemetry/events?station={station.slug}",
            metadata={"expects": "TelemetryEventCreate"},
        ),
        schemas.AgentAction(
            name="assign_source",
            description="Assign a telemetry source to the station.",
            endpoint=f"/api/v1/stations/{station.slug}/tasks",
            method="POST",
            metadata={"model": "StationAssignmentCreate"},
        ),
    ]
    return schemas.StationAgentCatalog(station=station, actions=actions)
