"""Telemetry CRUD router."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from .. import schemas
from ..services.supabase import (
    SupabaseApiError,
    SupabaseRepository,
    get_station_context,
    get_supabase_repository,
)

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


def list_sources(
    repo: SupabaseRepository = Depends(get_supabase_repository),
    station_slug: Optional[str] = Depends(get_station_context),
):
    try:
        return repo.list_telemetry_sources(station_slug=station_slug)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post(
    "/sources",
    response_model=schemas.TelemetrySourceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    payload: schemas.TelemetrySourceCreate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    try:
        return repo.create_telemetry_source(payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/sources/{source_id}", response_model=schemas.TelemetrySourceRead)
def read_source(
    source_id: int, repo: SupabaseRepository = Depends(get_supabase_repository)
):
    try:
        return repo.get_telemetry_source(source_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.patch("/sources/{source_id}", response_model=schemas.TelemetrySourceRead)
def update_source(
    source_id: int,
    payload: schemas.TelemetrySourceUpdate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    try:
        return repo.update_telemetry_source(source_id, payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: int, repo: SupabaseRepository = Depends(get_supabase_repository)
):
    try:
        repo.delete_telemetry_source(source_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return None


@router.get("/events", response_model=List[schemas.TelemetryEventWithSource])
def list_events(
    repo: SupabaseRepository = Depends(get_supabase_repository),
    station_slug: Optional[str] = Depends(get_station_context),
):
    try:
        return repo.list_telemetry_events(station_slug=station_slug)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc



@router.post(
    "/events",
    response_model=schemas.TelemetryEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    payload: schemas.TelemetryEventCreate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    try:
        return repo.create_telemetry_event(payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/events/{event_id}", response_model=schemas.TelemetryEventRead)
def read_event(
    event_id: int, repo: SupabaseRepository = Depends(get_supabase_repository)
):
    try:
        return repo.get_telemetry_event(event_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.patch("/events/{event_id}", response_model=schemas.TelemetryEventRead)
def update_event(
    event_id: int,
    payload: schemas.TelemetryEventUpdate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    try:
        return repo.update_telemetry_event(event_id, payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int, repo: SupabaseRepository = Depends(get_supabase_repository)
):
    try:
        repo.delete_telemetry_event(event_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return None
