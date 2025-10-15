from datetime import datetime
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TelemetrySource


router = APIRouter()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "source"


class TelemetrySourceBase(BaseModel):
    name: str = Field(..., description="Human friendly name")
    slug: Optional[str] = Field(None, description="Unique identifier used in URLs")
    source_type: str = Field(..., description="Connector type (adsb, ais, aprs, etc.)")
    description: Optional[str] = None
    connection_mode: str = Field(
        default="online",
        description="How the connector obtains data (online, offline)",
    )
    is_active: bool = True
    configuration: Optional[dict] = Field(
        default=None,
        description="Connector specific configuration payload",
    )


class TelemetrySourceCreate(TelemetrySourceBase):
    pass


class TelemetrySourceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    source_type: Optional[str] = None
    description: Optional[str] = None
    connection_mode: Optional[str] = None
    is_active: Optional[bool] = None
    configuration: Optional[dict] = None


class TelemetrySourceResponse(TelemetrySourceBase):
    id: int
    last_ingested_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TelemetrySourceResponse])
def list_sources(db: Session = Depends(get_db)) -> List[TelemetrySource]:
    return db.query(TelemetrySource).order_by(TelemetrySource.name.asc()).all()


@router.get("/{slug}", response_model=TelemetrySourceResponse)
def get_source(slug: str, db: Session = Depends(get_db)) -> TelemetrySource:
    source = db.query(TelemetrySource).filter(TelemetrySource.slug == slug).first()
    if not source:
        raise HTTPException(status_code=404, detail="Telemetry source not found")
    return source


@router.post("/", response_model=TelemetrySourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: TelemetrySourceCreate, db: Session = Depends(get_db)
) -> TelemetrySource:
    slug = payload.slug or _slugify(payload.name)
    existing = (
        db.query(TelemetrySource)
        .filter((TelemetrySource.slug == slug) | (TelemetrySource.name == payload.name))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A telemetry source with the same name or slug already exists",
        )

    db_source = TelemetrySource(
        name=payload.name,
        slug=slug,
        source_type=payload.source_type,
        description=payload.description,
        connection_mode=payload.connection_mode,
        is_active=payload.is_active,
        configuration=payload.configuration,
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.put("/{slug}", response_model=TelemetrySourceResponse)
def update_source(
    slug: str, payload: TelemetrySourceUpdate, db: Session = Depends(get_db)
) -> TelemetrySource:
    source = db.query(TelemetrySource).filter(TelemetrySource.slug == slug).first()
    if not source:
        raise HTTPException(status_code=404, detail="Telemetry source not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and not data.get("slug"):
        data.setdefault("slug", _slugify(data["name"]))

    if "slug" in data and data["slug"] != source.slug:
        conflict = (
            db.query(TelemetrySource)
            .filter(TelemetrySource.slug == data["slug"], TelemetrySource.id != source.id)
            .first()
        )
        if conflict:
            raise HTTPException(status_code=400, detail="Slug already in use")

    for key, value in data.items():
        setattr(source, key, value)

    source.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(slug: str, db: Session = Depends(get_db)) -> None:
    source = db.query(TelemetrySource).filter(TelemetrySource.slug == slug).first()
    if not source:
        raise HTTPException(status_code=404, detail="Telemetry source not found")

    db.delete(source)
    db.commit()

