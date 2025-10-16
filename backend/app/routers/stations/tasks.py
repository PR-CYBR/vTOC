"""Station task queues."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ... import schemas
from ...services.supabase import (
    SupabaseApiError,
    SupabaseRepository,
    get_supabase_repository,
)
from .dashboard import _get_station, _handle_supabase_error

router = APIRouter(prefix="/api/v1/stations", tags=["station-tasks"])


@router.get("/{station_slug}/tasks", response_model=schemas.StationTaskQueue)
def station_task_queue(
    station_slug: str,
    repo: SupabaseRepository = Depends(get_supabase_repository),
) -> schemas.StationTaskQueue:
    # Ensure station exists for consistent error behaviour
    station = _get_station(repo, station_slug)
    try:
        return repo.station_task_queue(station.slug)
    except SupabaseApiError as exc:
        _handle_supabase_error(exc)
