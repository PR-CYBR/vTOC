from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TelemetryEvent, TelemetrySource


router = APIRouter()


class TelemetryIngestPayload(BaseModel):
    event_time: Optional[datetime] = Field(
        default=None, description="Timestamp when the telemetry was recorded"
    )
    latitude: Optional[float] = Field(default=None, description="Latitude in decimal degrees")
    longitude: Optional[float] = Field(default=None, description="Longitude in decimal degrees")
    altitude: Optional[float] = Field(default=None, description="Altitude in meters")
    heading: Optional[float] = Field(default=None, description="Heading in degrees")
    speed: Optional[float] = Field(default=None, description="Speed in knots/meters per second")
    payload: Optional[Dict[str, Any]] = Field(
        default=None, description="Structured telemetry payload"
    )
    raw_data: Optional[str] = Field(
        default=None, description="Original raw message or file contents"
    )
    status: Optional[str] = Field(default="received")


class TelemetryIngestResponse(BaseModel):
    id: int
    source_id: int
    event_time: datetime
    received_at: datetime
    status: str

    class Config:
        from_attributes = True


@router.post("/{source_slug}", response_model=TelemetryIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_event(
    source_slug: str, payload: TelemetryIngestPayload, db: Session = Depends(get_db)
) -> TelemetryEvent:
    source = db.query(TelemetrySource).filter(TelemetrySource.slug == source_slug).first()
    if not source:
        raise HTTPException(status_code=404, detail="Telemetry source not found")

    if not source.is_active:
        raise HTTPException(status_code=409, detail="Telemetry source is disabled")

    now = datetime.utcnow()
    event_time = payload.event_time or now

    event = TelemetryEvent(
        source_id=source.id,
        event_time=event_time,
        received_at=now,
        latitude=payload.latitude,
        longitude=payload.longitude,
        altitude=payload.altitude,
        heading=payload.heading,
        speed=payload.speed,
        payload=payload.payload,
        raw_data=payload.raw_data,
        status=payload.status or "received",
    )

    source.last_ingested_at = now
    source.updated_at = now

    db.add(event)
    db.commit()
    db.refresh(event)

    return event

