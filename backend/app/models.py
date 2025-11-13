"""SQLAlchemy models for Telemetry entities."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .db import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    timezone = Column(String(100), nullable=False, default="UTC")
    telemetry_schema = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sources = relationship(
        "TelemetrySource",
        back_populates="station",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assignments = relationship(
        "StationAssignment",
        back_populates="station",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    events = relationship("TelemetryEvent", back_populates="station")
    base_station = relationship(
        "BaseStation",
        back_populates="station",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    devices = relationship(
        "Device",
        back_populates="station",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    overlays = relationship(
        "Overlay",
        back_populates="station",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TelemetrySource(Base):
    __tablename__ = "telemetry_sources"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
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

    station = relationship("Station", back_populates="sources")
    assignments = relationship(
        "StationAssignment",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    events = relationship(
        "TelemetryEvent",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    rf_streams = relationship(
        "RfStream",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    gps_fixes = relationship(
        "TelemetryGpsFix",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    aircraft_positions = relationship(
        "TelemetryAircraftPosition",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("telemetry_sources.id", ondelete="CASCADE"))
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
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
    station = relationship("Station", back_populates="events")


class StationAssignment(Base):
    __tablename__ = "station_assignments"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"))
    source_id = Column(Integer, ForeignKey("telemetry_sources.id", ondelete="CASCADE"))
    role = Column(String(100), nullable=False, default="primary")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    station = relationship("Station", back_populates="assignments")
    source = relationship("TelemetrySource", back_populates="assignments")


class BaseStation(Base):
    __tablename__ = "base_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude_m = Column(Float, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    station = relationship("Station", back_populates="base_station")
    devices = relationship(
        "Device",
        back_populates="base_station",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    base_station_id = Column(Integer, ForeignKey("base_stations.id", ondelete="SET NULL"), nullable=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    device_type = Column(String(100), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    firmware_version = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime, nullable=True)
    configuration = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    base_station = relationship("BaseStation", back_populates="devices")
    station = relationship("Station", back_populates="devices")
    rf_streams = relationship(
        "RfStream",
        back_populates="device",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    gps_fixes = relationship(
        "TelemetryGpsFix",
        back_populates="device",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    aircraft_positions = relationship(
        "TelemetryAircraftPosition",
        back_populates="device",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RfStream(Base):
    __tablename__ = "rf_streams"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    source_id = Column(Integer, ForeignKey("telemetry_sources.id", ondelete="SET NULL"), nullable=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    center_frequency_hz = Column(BigInteger, nullable=True)
    bandwidth_hz = Column(BigInteger, nullable=True)
    sample_rate = Column(BigInteger, nullable=True)
    modulation = Column(String(100), nullable=True)
    gain = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    configuration = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = relationship("Device", back_populates="rf_streams")
    source = relationship("TelemetrySource", back_populates="rf_streams")


class Overlay(Base):
    __tablename__ = "overlays"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"))
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    overlay_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    configuration = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    station = relationship("Station", back_populates="overlays")


class TelemetryGpsFix(Base):
    __tablename__ = "gps_fixes"
    __table_args__ = {"schema": "telemetry"}

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("telemetry_sources.id", ondelete="SET NULL"), nullable=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    horizontal_accuracy = Column(Float, nullable=True)
    vertical_accuracy = Column(Float, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("TelemetrySource", back_populates="gps_fixes")
    station = relationship("Station")
    device = relationship("Device", back_populates="gps_fixes")


class TelemetryAircraftPosition(Base):
    __tablename__ = "aircraft_positions"
    __table_args__ = {"schema": "telemetry"}

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("telemetry_sources.id", ondelete="SET NULL"), nullable=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    icao_address = Column(String(6), nullable=True)
    callsign = Column(String(16), nullable=True)
    squawk = Column(String(8), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    ground_speed = Column(Float, nullable=True)
    vertical_rate = Column(Float, nullable=True)
    position_time = Column(DateTime, default=datetime.utcnow, index=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("TelemetrySource", back_populates="aircraft_positions")
    station = relationship("Station")
    device = relationship("Device", back_populates="aircraft_positions")


class PersonOfInterest(Base):
    """Person, vehicle, or device of interest for tracking."""
    __tablename__ = "poi"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, default="person")  # person, vehicle, device
    risk_level = Column(String(100), nullable=False, default="info")  # info, watch, hostile
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    identifiers = relationship(
        "PoiIdentifier",
        back_populates="poi",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    imei_watch_entries = relationship(
        "ImeiWatchEntry",
        back_populates="linked_poi",
        foreign_keys="ImeiWatchEntry.linked_poi_id",
    )


class PoiIdentifier(Base):
    """Identifier associated with a POI (IMEI, MAC, callsign, phone, etc)."""
    __tablename__ = "poi_identifier"

    id = Column(Integer, primary_key=True, index=True)
    poi_id = Column(Integer, ForeignKey("poi.id", ondelete="CASCADE"), nullable=False)
    identifier_type = Column(String(100), nullable=False)  # imei, mac, callsign, phone
    identifier_value = Column(String(255), nullable=False, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    poi = relationship("PersonOfInterest", back_populates="identifiers")


class ImeiWatchEntry(Base):
    """IMEI watchlist entry for whitelist or blacklist."""
    __tablename__ = "imei_watch_entry"

    id = Column(Integer, primary_key=True, index=True)
    identifier_value = Column(String(255), nullable=False, unique=True, index=True)
    list_type = Column(String(50), nullable=False)  # whitelist or blacklist
    label = Column(String(255), nullable=True)
    linked_poi_id = Column(Integer, ForeignKey("poi.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    linked_poi = relationship("PersonOfInterest", back_populates="imei_watch_entries", foreign_keys=[linked_poi_id])
