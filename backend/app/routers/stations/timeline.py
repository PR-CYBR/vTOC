"""Station timeline endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ... import schemas
from ...services.supabase import (
    SupabaseApiError,
    SupabaseRepository,
    get_supabase_repository,
)

router = APIRouter(prefix="/api/v1/stations", tags=["station-timeline"])


@router.get(
    "/{station_slug}/timeline",
    response_model=schemas.StationTimelinePage,
    status_code=status.HTTP_200_OK,
)
def station_timeline(
    station_slug: str,
    limit: int = Query(50, ge=0, le=200),
    offset: int = Query(0, ge=0),
    repo: SupabaseRepository = Depends(get_supabase_repository),
) -> schemas.StationTimelinePage:
    """Return a merged timeline of telemetry and agent activity for a station."""

    try:
        return repo.list_station_timeline_entries(
            station_slug, limit=limit, offset=offset
        )
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


__all__ = ["router", "station_timeline"]
