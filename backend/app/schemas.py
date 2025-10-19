"""Pydantic schemas for telemetry API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .schema_mixins import (
    ActivationFields,
    DescriptionMixin,
    IdentifierMixin,
    ORMModelMixin,
    SlugNameMixin,
    TimestampsMixin,
    create_partial_model,
)


class StationBase(SlugNameMixin, DescriptionMixin):
    timezone: str = "UTC"
    telemetry_schema: Optional[str] = None


class StationCreate(StationBase):
    pass


StationUpdate = create_partial_model("StationUpdate", StationBase)


class StationRead(ORMModelMixin, StationBase, IdentifierMixin, TimestampsMixin):
    pass


class BaseStationBase(SlugNameMixin, DescriptionMixin):
    status: str = "active"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None
    station_id: Optional[int] = None


class BaseStationCreate(BaseStationBase):
    station_id: int


BaseStationUpdate = create_partial_model("BaseStationUpdate", BaseStationBase)


class BaseStationRead(ORMModelMixin, BaseStationBase, IdentifierMixin, TimestampsMixin):
    pass


class TelemetrySourceBase(SlugNameMixin, DescriptionMixin, ActivationFields):
    source_type: str
    connection_mode: str = "online"
    configuration: Optional[dict[str, Any]] = None
    station_id: Optional[int] = None


class TelemetrySourceCreate(TelemetrySourceBase):
    pass


TelemetrySourceUpdate = create_partial_model("TelemetrySourceUpdate", TelemetrySourceBase)


class TelemetrySourceRead(
    ORMModelMixin, TelemetrySourceBase, IdentifierMixin, TimestampsMixin
):
    last_ingested_at: Optional[datetime] = None
    station: Optional[StationRead] = None


class DeviceBase(SlugNameMixin, ActivationFields):
    device_type: str
    base_station_id: Optional[int] = None
    station_id: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    configuration: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class DeviceCreate(DeviceBase):
    pass


DeviceUpdate = create_partial_model("DeviceUpdate", DeviceBase)


class DeviceRead(ORMModelMixin, DeviceBase, IdentifierMixin, TimestampsMixin):
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
    status: Optional[str] = "received"
    station_id: Optional[int] = None


class TelemetryEventCreate(TelemetryEventBase):
    source_id: Optional[int] = None
    source_slug: Optional[str] = None
    source_name: Optional[str] = None


TelemetryEventUpdate = create_partial_model(
    "TelemetryEventUpdate", TelemetryEventBase, exclude={"station_id"}
)


class TelemetryEventRead(ORMModelMixin, TelemetryEventBase):
    id: int
    received_at: datetime


class RfStreamBase(SlugNameMixin, DescriptionMixin, ActivationFields):
    device_id: int
    source_id: Optional[int] = None
    center_frequency_hz: Optional[int] = None
    bandwidth_hz: Optional[int] = None
    sample_rate: Optional[int] = None
    modulation: Optional[str] = None
    gain: Optional[float] = None
    configuration: Optional[dict[str, Any]] = None


class RfStreamCreate(RfStreamBase):
    pass


RfStreamUpdate = create_partial_model("RfStreamUpdate", RfStreamBase)


class RfStreamRead(ORMModelMixin, RfStreamBase, IdentifierMixin, TimestampsMixin):
    pass


class TelemetryEventWithSource(TelemetryEventRead):
    source: TelemetrySourceRead
    station: Optional[StationRead] = None


class OverlayBase(SlugNameMixin, DescriptionMixin, ActivationFields):
    station_id: int
    overlay_type: str
    configuration: Optional[dict[str, Any]] = None


class OverlayCreate(OverlayBase):
    pass


OverlayUpdate = create_partial_model("OverlayUpdate", OverlayBase)


class OverlayRead(ORMModelMixin, OverlayBase, IdentifierMixin, TimestampsMixin):
    pass


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


class TelemetryGpsFixRead(ORMModelMixin, TelemetryGpsFixBase):
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


class TelemetryAircraftPositionRead(ORMModelMixin, TelemetryAircraftPositionBase):
    id: int
    position_time: datetime
    received_at: datetime
    created_at: datetime


class StationAssignmentBase(ActivationFields):
    station_id: int
    source_id: int
    role: str = "primary"


class StationAssignmentCreate(StationAssignmentBase):
    pass


class StationAssignmentRead(
    ORMModelMixin, StationAssignmentBase, IdentifierMixin, TimestampsMixin
):
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


AgentActionAuditUpdate = create_partial_model(
    "AgentActionAuditUpdate",
    AgentActionAuditBase,
    exclude={"action_id"},
    additional_fields={"completed_at": (Optional[datetime], None)},
)


class AgentActionAuditRead(
    ORMModelMixin, AgentActionAuditBase, IdentifierMixin, TimestampsMixin
):
    completed_at: Optional[datetime] = None
