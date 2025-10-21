"""Station AgentKit affordances."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ... import schemas
from ...services.supabase import (
    SupabaseApiError,
    SupabaseRepository,
    get_supabase_repository,
)
from .dashboard import _get_station, _handle_supabase_error

router = APIRouter(prefix="/api/v1/stations", tags=["station-agentkit"])


@router.get(
    "/{station_slug}/agentkit/actions",
    response_model=schemas.StationAgentCatalog,
)
def station_agent_actions(
    station_slug: str, repo: SupabaseRepository = Depends(get_supabase_repository)
) -> schemas.StationAgentCatalog:
    try:
        station = _get_station(repo, station_slug)
    except SupabaseApiError as exc:
        _handle_supabase_error(exc)
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
        schemas.AgentAction(
            name="mission_timeline",
            description=(
                "Retrieve the station's consolidated mission timeline, including telemetry, "
                "AgentKit summaries, and operator log entries."
            ),
            endpoint=f"/api/v1/stations/{station.slug}/mission-timeline",
            method="GET",
            metadata={
                "path_params": {
                    "station_slug": {
                        "type": "string",
                        "required": True,
                        "description": "Slug identifying the station mission context.",
                    }
                },
                "query": {
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "default": 50,
                        "minimum": 1,
                        "description": (
                            "Maximum number of timeline entries to return (newest first)."
                        ),
                    }
                },
                "response": {
                    "type": "array",
                    "description": (
                        "Timeline entries ordered from newest to oldest. Each entry includes "
                        "an identifier, occurrence timestamp, category, human-readable "
                        "summary, and structured metadata payload when available."
                    ),
                },
            },
        ),
    ]
    return schemas.StationAgentCatalog(station=station, actions=actions)
