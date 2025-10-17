"""ChatKit action handlers for hardware management."""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.app.services.hardware import (
    AdsbToggleRequest,
    BaseStationRegistration,
    GpsTestRequest,
    H4MImportRequest,
    HardwareManager,
    HardwareOperationError,
    HardwareStatus,
    get_hardware_manager,
)


class HardwareActionError(RuntimeError):
    """Raised when a ChatKit hardware action cannot be fulfilled."""


def _resolve_manager(manager: Optional[HardwareManager] = None) -> HardwareManager:
    return manager or get_hardware_manager()


async def hw_list_serial(manager: Optional[HardwareManager] = None) -> Dict[str, Any]:
    mgr = _resolve_manager(manager)
    ports = mgr.list_serial_ports()
    return {"ports": [port.model_dump() for port in ports]}


async def hw_test_gps(
    payload: Dict[str, Any], manager: Optional[HardwareManager] = None
) -> Dict[str, Any]:
    mgr = _resolve_manager(manager)
    request = GpsTestRequest.model_validate(payload)
    result = mgr.test_gps(request)
    data = result.model_dump()
    if not result.success:
        raise HardwareActionError(result.error or "GPS test failed")
    return data


async def hw_register_base_station(
    payload: Dict[str, Any], manager: Optional[HardwareManager] = None
) -> Dict[str, Any]:
    mgr = _resolve_manager(manager)
    registration = BaseStationRegistration.model_validate(payload)
    try:
        stored = mgr.register_base_station(registration)
    except HardwareOperationError as exc:
        raise HardwareActionError(str(exc)) from exc
    return stored.model_dump()


async def hw_enable_adsb(
    payload: Dict[str, Any], manager: Optional[HardwareManager] = None
) -> Dict[str, Any]:
    mgr = _resolve_manager(manager)
    request = AdsbToggleRequest.model_validate(payload)
    try:
        config = mgr.enable_adsb(request)
    except HardwareOperationError as exc:
        raise HardwareActionError(str(exc)) from exc
    return config.model_dump()


async def hw_status(manager: Optional[HardwareManager] = None) -> Dict[str, Any]:
    mgr = _resolve_manager(manager)
    status: HardwareStatus = mgr.get_status()
    return status.model_dump()


async def h4m_import(
    payload: Dict[str, Any], manager: Optional[HardwareManager] = None
) -> Dict[str, Any]:
    mgr = _resolve_manager(manager)
    request = H4MImportRequest.model_validate(payload)
    try:
        result = mgr.import_h4m(request)
    except HardwareOperationError as exc:
        raise HardwareActionError(str(exc)) from exc
    return result.model_dump()
