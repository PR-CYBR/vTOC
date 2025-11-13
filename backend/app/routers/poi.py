"""POI (Person of Interest) CRUD router."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from .. import schemas
from ..services.supabase import (
    SupabaseApiError,
    SupabaseRepository,
    get_supabase_repository,
)

router = APIRouter(prefix="/api/v1/poi", tags=["poi"])


@router.get("", response_model=List[schemas.PoiRead])
def list_poi(
    is_active: bool | None = None,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """List all persons of interest."""
    try:
        return repo.list_poi(is_active=is_active)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("", response_model=schemas.PoiRead, status_code=status.HTTP_201_CREATED)
def create_poi(
    payload: schemas.PoiCreate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Create a new person of interest."""
    try:
        return repo.create_poi(payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/{poi_id}", response_model=schemas.PoiRead)
def get_poi(
    poi_id: int,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Get a specific person of interest."""
    try:
        return repo.get_poi(poi_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.patch("/{poi_id}", response_model=schemas.PoiRead)
def update_poi(
    poi_id: int,
    payload: schemas.PoiUpdate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Update a person of interest."""
    try:
        return repo.update_poi(poi_id, payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.delete("/{poi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poi(
    poi_id: int,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Delete a person of interest."""
    try:
        repo.delete_poi(poi_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return None


# POI Identifier endpoints
@router.post("/{poi_id}/identifiers", response_model=schemas.PoiIdentifierRead, status_code=status.HTTP_201_CREATED)
def create_poi_identifier(
    poi_id: int,
    payload: schemas.PoiIdentifierCreate,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Add an identifier to a person of interest."""
    # Ensure the poi_id in the payload matches the path parameter
    if payload.poi_id != poi_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="POI ID in payload must match path parameter"
        )
    try:
        return repo.create_poi_identifier(payload)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/{poi_id}/identifiers", response_model=List[schemas.PoiIdentifierRead])
def list_poi_identifiers(
    poi_id: int,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """List all identifiers for a person of interest."""
    try:
        return repo.list_poi_identifiers(poi_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.delete("/{poi_id}/identifiers/{identifier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poi_identifier(
    poi_id: int,
    identifier_id: int,
    repo: SupabaseRepository = Depends(get_supabase_repository),
):
    """Remove an identifier from a person of interest."""
    try:
        repo.delete_poi_identifier(poi_id, identifier_id)
    except SupabaseApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return None


__all__ = ["router"]
