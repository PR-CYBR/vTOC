"""SQLAlchemy models for Telemetry entities."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .db import Base


class TelemetrySource(Base):
    __tablename__ = "telemetry_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    source_type = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    connection_mode = Column(String(50), default="online")
    configuration = Column(JSON, nullable=True)
    last_ingested_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship(
        "TelemetryEvent",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("telemetry_sources.id", ondelete="CASCADE"))
    event_time = Column(DateTime, default=datetime.utcnow, index=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    payload = Column(JSON, nullable=True)
    raw_data = Column(Text, nullable=True)
    status = Column(String(50), default="received")

    source = relationship("TelemetrySource", back_populates="events")
