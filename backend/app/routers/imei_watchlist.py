"""IMEI watchlist CRUD router."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from .. import schemas
from ..services.supabase import (
    SupabaseApiError,
    SupabaseRepository,
    get_supabase_repository,
)

router = APIRouter(prefix="/api/v1/imei-watchlist", tags=["imei-watchlist"])


@router.get("", response_model=List[schemas.ImeiWatchEntryRead])
def list_imei_watchlist(
    list_type: str | None = None,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """List IMEI watchlist entries."""
    try:
        return repo.list_imei_watchlist(list_type=list_type)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("", response_model=schemas.ImeiWatchEntryRead, status_code=status.HTTP_201_CREATED)
def create_imei_watch_entry(
    payload: schemas.ImeiWatchEntryCreate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Create a new IMEI watchlist entry."""
    try:
        return repo.create_imei_watch_entry(payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/{entry_id}", response_model=schemas.ImeiWatchEntryRead)
def get_imei_watch_entry(
    entry_id: int,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Get a specific IMEI watchlist entry."""
    try:
        return repo.get_imei_watch_entry(entry_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.patch("/{entry_id}", response_model=schemas.ImeiWatchEntryRead)
def update_imei_watch_entry(
    entry_id: int,
    payload: schemas.ImeiWatchEntryUpdate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Update an IMEI watchlist entry."""
    try:
        return repo.update_imei_watch_entry(entry_id, payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imei_watch_entry(
    entry_id: int,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Delete an IMEI watchlist entry."""
    try:
        repo.delete_imei_watch_entry(entry_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return None


@router.get("/check/{imei}", response_model=schemas.ImeiWatchEntryRead | None)
def check_imei(
    imei: str,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Check if an IMEI is on the watchlist."""
    try:
        return repo.check_imei_watchlist(imei)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


__all__ = ["router"]
