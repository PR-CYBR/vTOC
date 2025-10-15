"""Pydantic schemas for telemetry API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StationBase(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    timezone: str = "UTC"
    telemetry_schema: Optional[str] = None


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    timezone: Optional[str] = None
    telemetry_schema: Optional[str] = None


class StationRead(StationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TelemetrySourceBase(BaseModel):
    name: str
    slug: str
    source_type: str
    description: Optional[str] = None
    is_active: bool = True
    connection_mode: str = "online"
    configuration: Optional[dict] = None
    station_id: Optional[int] = None


class TelemetrySourceCreate(TelemetrySourceBase):
    pass


class TelemetrySourceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    source_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    connection_mode: Optional[str] = None
    configuration: Optional[dict] = None
    station_id: Optional[int] = None


class TelemetrySourceRead(TelemetrySourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_ingested_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    station: Optional[StationRead] = None


class TelemetryEventBase(BaseModel):
    event_time: Optional[datetime] = None
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    altitude: Optional[float] = Field(default=None)
    heading: Optional[float] = Field(default=None)
    speed: Optional[float] = Field(default=None)
    payload: Optional[dict] = None
    raw_data: Optional[str] = None
    status: Optional[str] = 'received'
    station_id: Optional[int] = None


class TelemetryEventCreate(TelemetryEventBase):
    source_id: Optional[int] = None
    source_slug: Optional[str] = None
    source_name: Optional[str] = None


class TelemetryEventUpdate(BaseModel):
    event_time: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    payload: Optional[dict] = None
    raw_data: Optional[str] = None
    status: Optional[str] = None


class TelemetryEventRead(TelemetryEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    received_at: datetime


class TelemetryEventWithSource(TelemetryEventRead):
    source: TelemetrySourceRead
    station: Optional[StationRead] = None


class StationAssignmentBase(BaseModel):
    station_id: int
    source_id: int
    role: str = "primary"
    is_active: bool = True


class StationAssignmentCreate(StationAssignmentBase):
    pass


class StationAssignmentRead(StationAssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    station: StationRead
    source: TelemetrySourceRead


class StationDashboardMetrics(BaseModel):
    total_events: int
    active_sources: int
    last_event: Optional[TelemetryEventRead] = None


class StationDashboard(BaseModel):
    station: StationRead
    metrics: StationDashboardMetrics


class StationTask(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    created_at: datetime
    due_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StationTaskQueue(BaseModel):
    station: StationRead
    tasks: List[StationTask]


class AgentAction(BaseModel):
    name: str
    description: str
    endpoint: str
    method: str = "POST"
    metadata: dict[str, Any] = Field(default_factory=dict)


class StationAgentCatalog(BaseModel):
    station: StationRead
    actions: List[AgentAction]
