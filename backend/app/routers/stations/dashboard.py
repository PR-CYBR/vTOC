"""Station dashboard endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ... import schemas
from ...services.supabase import (
    SupabaseApiError,
    SupabaseRepository,
    get_supabase_repository,
)

router = APIRouter(prefix="/api/v1/stations", tags=["station-dashboard"])


def _handle_supabase_error(exc: SupabaseApiError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


def _get_station(repo: SupabaseRepository, station_slug: str) -> schemas.StationRead:
    try:
        return repo.get_station(station_slug)
    except SupabaseApiError as exc:
        _handle_supabase_error(exc)


@router.get("/", response_model=List[schemas.StationRead])
def list_stations(
    repo: SupabaseRepository = Depends(get_supabase_repository),
) -> List[schemas.StationRead]:
    try:
        return repo.list_stations()
    except SupabaseApiError as exc:
        _handle_supabase_error(exc)


@router.get("/{station_slug}", response_model=schemas.StationRead)
def read_station(
    station_slug: str,
    repo: SupabaseRepository = Depends(get_supabase_repository),
) -> schemas.StationRead:
    return _get_station(repo, station_slug)


@router.get("/{station_slug}/dashboard", response_model=schemas.StationDashboard)
def station_dashboard(
    station_slug: str,
    repo: SupabaseRepository = Depends(get_supabase_repository),
) -> schemas.StationDashboard:
    try:
        return repo.station_dashboard(station_slug)
    except SupabaseApiError as exc:
        _handle_supabase_error(exc)
