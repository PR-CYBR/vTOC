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


class BaseStationBase(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    status: str = "active"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None
    station_id: Optional[int] = None


class BaseStationCreate(BaseStationBase):
    station_id: int


class BaseStationUpdate(BaseModel):
    slug: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None
    station_id: Optional[int] = None


class BaseStationRead(BaseStationBase):
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


class DeviceBase(BaseModel):
    slug: str
    name: str
    device_type: str
    base_station_id: Optional[int] = None
    station_id: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    is_active: bool = True
    last_seen_at: Optional[datetime] = None
    configuration: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    slug: Optional[str] = None
    name: Optional[str] = None
    device_type: Optional[str] = None
    base_station_id: Optional[int] = None
    station_id: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    is_active: Optional[bool] = None
    last_seen_at: Optional[datetime] = None
    configuration: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class DeviceRead(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    base_station: Optional[BaseStationRead] = None
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


class RfStreamBase(BaseModel):
    slug: str
    name: str
    device_id: int
    source_id: Optional[int] = None
    description: Optional[str] = None
    center_frequency_hz: Optional[int] = None
    bandwidth_hz: Optional[int] = None
    sample_rate: Optional[int] = None
    modulation: Optional[str] = None
    gain: Optional[float] = None
    is_active: bool = True
    configuration: Optional[dict[str, Any]] = None


class RfStreamCreate(RfStreamBase):
    pass


class RfStreamUpdate(BaseModel):
    slug: Optional[str] = None
    name: Optional[str] = None
    device_id: Optional[int] = None
    source_id: Optional[int] = None
    description: Optional[str] = None
    center_frequency_hz: Optional[int] = None
    bandwidth_hz: Optional[int] = None
    sample_rate: Optional[int] = None
    modulation: Optional[str] = None
    gain: Optional[float] = None
    is_active: Optional[bool] = None
    configuration: Optional[dict[str, Any]] = None


class RfStreamRead(RfStreamBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TelemetryEventWithSource(TelemetryEventRead):
    source: TelemetrySourceRead
    station: Optional[StationRead] = None


class OverlayBase(BaseModel):
    slug: str
    name: str
    station_id: int
    overlay_type: str
    description: Optional[str] = None
    configuration: Optional[dict[str, Any]] = None
    is_active: bool = True


class OverlayCreate(OverlayBase):
    pass


class OverlayUpdate(BaseModel):
    slug: Optional[str] = None
    name: Optional[str] = None
    station_id: Optional[int] = None
    overlay_type: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class OverlayRead(OverlayBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TelemetryGpsFixBase(BaseModel):
    source_id: Optional[int] = None
    station_id: Optional[int] = None
    device_id: Optional[int] = None
    recorded_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    horizontal_accuracy: Optional[float] = None
    vertical_accuracy: Optional[float] = None
    raw_payload: Optional[dict[str, Any]] = None


class TelemetryGpsFixCreate(TelemetryGpsFixBase):
    pass


class TelemetryGpsFixRead(TelemetryGpsFixBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: datetime
    created_at: datetime


class TelemetryAircraftPositionBase(BaseModel):
    source_id: Optional[int] = None
    station_id: Optional[int] = None
    device_id: Optional[int] = None
    icao_address: Optional[str] = None
    callsign: Optional[str] = None
    squawk: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    ground_speed: Optional[float] = None
    vertical_rate: Optional[float] = None
    position_time: Optional[datetime] = None
    received_at: Optional[datetime] = None
    raw_payload: Optional[dict[str, Any]] = None


class TelemetryAircraftPositionCreate(TelemetryAircraftPositionBase):
    pass


class TelemetryAircraftPositionRead(TelemetryAircraftPositionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position_time: datetime
    received_at: datetime
    created_at: datetime


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


class AgentTool(BaseModel):
    name: str
    description: str
    signature: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentActionExecuteRequest(BaseModel):
    tool_name: str
    action_input: dict[str, Any]
    metadata: dict[str, Any] | None = None


class AgentActionExecuteResponse(BaseModel):
    action_id: str
    status: str
    result: Optional[dict[str, Any]] = None
    message: Optional[str] = None


class AgentActionWebhookEvent(BaseModel):
    action_id: str
    status: str
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class AgentActionAuditBase(BaseModel):
    action_id: str
    tool_name: str
    status: str
    request_payload: Optional[dict[str, Any]] = None
    response_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None


class AgentActionAuditCreate(AgentActionAuditBase):
    completed_at: Optional[datetime] = None


class AgentActionAuditUpdate(BaseModel):
    tool_name: Optional[str] = None
    status: Optional[str] = None
    request_payload: Optional[dict[str, Any]] = None
    response_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class AgentActionAuditRead(AgentActionAuditBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
