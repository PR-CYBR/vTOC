from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
    JSON,
    Float,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Operation(Base):
    """Operation model for tactical operations"""
    __tablename__ = "operations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code_name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    status = Column(String(50), default="planning")  # planning, active, completed, cancelled
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    missions = relationship("Mission", back_populates="operation")

class Mission(Base):
    """Mission model for specific tasks within operations"""
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(Integer, ForeignKey("operations.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    priority = Column(String(20), default="medium")
    assigned_to = Column(String(100))
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    operation = relationship("Operation", back_populates="missions")
    intel_reports = relationship("IntelReport", back_populates="mission")

class Asset(Base):
    """Asset model for tracking resources and equipment"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(100))  # personnel, vehicle, equipment, drone, etc.
    status = Column(String(50), default="available")  # available, deployed, maintenance, retired
    location = Column(String(255))
    specifications = Column(JSON)
    assigned_to = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IntelReport(Base):
    """Intelligence report model"""
    __tablename__ = "intel_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    classification = Column(String(50), default="unclassified")  # unclassified, confidential, secret
    source = Column(String(255))
    reliability = Column(String(50))  # verified, probable, possible, doubtful
    reported_by = Column(String(100))
    report_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mission = relationship("Mission", back_populates="intel_reports")

class Agent(Base):
    """Agent model for automation agents"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    agent_type = Column(String(100))  # monitor, analyzer, executor, coordinator
    status = Column(String(50), default="idle")  # idle, running, error, stopped
    description = Column(Text)
    configuration = Column(JSON)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TelemetrySource(Base):
    """Telemetry data source configuration"""

    __tablename__ = "telemetry_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    source_type = Column(String(100), nullable=False)  # adsb, ais, aprs, etc.
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    connection_mode = Column(String(50), default="online")  # online, offline
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
    """Individual telemetry readings captured from a source"""

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
