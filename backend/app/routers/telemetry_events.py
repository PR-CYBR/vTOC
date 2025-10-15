from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TelemetryEvent, TelemetrySource


router = APIRouter()


class TelemetryEventResponse(BaseModel):
    id: int
    source_id: int
    event_time: datetime
    received_at: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]
    heading: Optional[float]
    speed: Optional[float]
    payload: Optional[dict]
    raw_data: Optional[str]
    status: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TelemetryEventResponse])
def list_events(
    db: Session = Depends(get_db),
    source: Optional[str] = Query(None, description="Filter by source slug"),
    since: Optional[datetime] = Query(None, description="Return events after this timestamp"),
    until: Optional[datetime] = Query(None, description="Return events before this timestamp"),
    limit: int = Query(100, gt=0, le=1000),
) -> List[TelemetryEvent]:
    query = db.query(TelemetryEvent).order_by(TelemetryEvent.event_time.desc())

    if source:
        telemetry_source = (
            db.query(TelemetrySource).filter(TelemetrySource.slug == source).first()
        )
        if not telemetry_source:
            raise HTTPException(status_code=404, detail="Telemetry source not found")
        query = query.filter(TelemetryEvent.source_id == telemetry_source.id)

    if since:
        query = query.filter(TelemetryEvent.event_time >= since)

    if until:
        query = query.filter(TelemetryEvent.event_time <= until)

    return query.limit(limit).all()


@router.get("/{event_id}", response_model=TelemetryEventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)) -> TelemetryEvent:
    event = db.query(TelemetryEvent).filter(TelemetryEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Telemetry event not found")
    return event

