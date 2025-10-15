"""Telemetry CRUD router."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..db import get_db

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


@router.get("/sources", response_model=List[schemas.TelemetrySourceRead])
def list_sources(db: Session = Depends(get_db)):
    return db.query(models.TelemetrySource).order_by(models.TelemetrySource.name).all()


@router.post(
    "/sources",
    response_model=schemas.TelemetrySourceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    payload: schemas.TelemetrySourceCreate, db: Session = Depends(get_db)
):
    instance = models.TelemetrySource(**payload.model_dump())
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


@router.get("/sources/{source_id}", response_model=schemas.TelemetrySourceRead)
def read_source(source_id: int, db: Session = Depends(get_db)):
    instance = db.get(models.TelemetrySource, source_id)
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return instance


@router.patch("/sources/{source_id}", response_model=schemas.TelemetrySourceRead)
def update_source(
    source_id: int,
    payload: schemas.TelemetrySourceUpdate,
    db: Session = Depends(get_db),
):
    instance = db.get(models.TelemetrySource, source_id)
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, key, value)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    instance = db.get(models.TelemetrySource, source_id)
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    db.delete(instance)
    db.commit()
    return None


@router.get("/events", response_model=List[schemas.TelemetryEventWithSource])
def list_events(db: Session = Depends(get_db)):
    query = (
        db.query(models.TelemetryEvent)
        .options(selectinload(models.TelemetryEvent.source))
        .order_by(models.TelemetryEvent.event_time.desc())
    )
    return query.limit(100).all()



@router.post(
    "/events",
    response_model=schemas.TelemetryEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_event(payload: schemas.TelemetryEventCreate, db: Session = Depends(get_db)):
    source = None
    if payload.source_id is not None:
        source = db.get(models.TelemetrySource, payload.source_id)
    elif payload.source_slug:
        source = (
            db.query(models.TelemetrySource)
            .filter(models.TelemetrySource.slug == payload.source_slug)
            .one_or_none()
        )
        if source is None and payload.source_name:
            source = models.TelemetrySource(
                name=payload.source_name,
                slug=payload.source_slug,
                source_type="external",
                description="Created via telemetry ingestion",
            )
            db.add(source)
            db.commit()
            db.refresh(source)
    if source is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown source")
    data = payload.model_dump(exclude={"source_id", "source_slug", "source_name"}, exclude_none=True)
    data["source_id"] = source.id
    instance = models.TelemetryEvent(**data)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


@router.get("/events/{event_id}", response_model=schemas.TelemetryEventRead)
def read_event(event_id: int, db: Session = Depends(get_db)):
    instance = (
        db.query(models.TelemetryEvent)
        .options(selectinload(models.TelemetryEvent.source))
        .filter(models.TelemetryEvent.id == event_id)
        .one_or_none()
    )
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return instance


@router.patch("/events/{event_id}", response_model=schemas.TelemetryEventRead)
def update_event(
    event_id: int,
    payload: schemas.TelemetryEventUpdate,
    db: Session = Depends(get_db),
):
    instance = (
        db.query(models.TelemetryEvent)
        .options(selectinload(models.TelemetryEvent.source))
        .filter(models.TelemetryEvent.id == event_id)
        .one_or_none()
    )
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, key, value)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    instance = (
        db.query(models.TelemetryEvent)
        .options(selectinload(models.TelemetryEvent.source))
        .filter(models.TelemetryEvent.id == event_id)
        .one_or_none()
    )
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    db.delete(instance)
    db.commit()
    return None
