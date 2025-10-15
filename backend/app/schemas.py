"""Pydantic schemas for telemetry API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class TelemetrySourceBase(BaseModel):
    name: str
    slug: str
    source_type: str
    description: Optional[str] = None
    is_active: bool = True
    connection_mode: str = "online"
    configuration: Optional[dict] = None


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


class TelemetrySourceRead(TelemetrySourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_ingested_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


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


class AgentTool(BaseModel):
    name: str
    description: str
    signature: Dict[str, Any]
    category: Optional[str] = None


class AgentActionExecuteRequest(BaseModel):
    tool_name: str
    action_input: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class AgentActionExecuteResponse(BaseModel):
    action_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class AgentActionWebhookEvent(BaseModel):
    action_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentActionAuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_id: str
    tool_name: str
    status: str
    request_payload: Optional[Dict[str, Any]] = None
    response_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
