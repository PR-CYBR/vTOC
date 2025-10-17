"""Hardware management endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..services.hardware import (
    AdsbConfig,
    AdsbToggleRequest,
    BaseStationConfig,
    BaseStationRegistration,
    GpsTestRequest,
    GpsTestResult,
    H4MImportRequest,
    H4MImportResult,
    HardwareManager,
    HardwareOperationError,
    HardwareStatus,
    SerialPortInfo,
    get_hardware_manager,
)

router = APIRouter(prefix="/api/v1/hardware", tags=["hardware"])


@router.get("/serial", response_model=List[SerialPortInfo])
def hw_list_serial(
    manager: HardwareManager = Depends(get_hardware_manager),
) -> List[SerialPortInfo]:
    return manager.list_serial_ports()


@router.post("/test-gps", response_model=GpsTestResult)
def hw_test_gps(
    request: GpsTestRequest,
    manager: HardwareManager = Depends(get_hardware_manager),
) -> GpsTestResult:
    return manager.test_gps(request)


@router.post(
    "/register-base-station",
    response_model=BaseStationConfig,
    status_code=status.HTTP_201_CREATED,
)
def hw_register_base_station(
    registration: BaseStationRegistration,
    manager: HardwareManager = Depends(get_hardware_manager),
) -> BaseStationConfig:
    try:
        return manager.register_base_station(registration)
    except HardwareOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post("/enable-adsb", response_model=AdsbConfig)
def hw_enable_adsb(
    request: AdsbToggleRequest,
    manager: HardwareManager = Depends(get_hardware_manager),
) -> AdsbConfig:
    try:
        return manager.enable_adsb(request)
    except HardwareOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get("/status", response_model=HardwareStatus)
def hw_status(
    manager: HardwareManager = Depends(get_hardware_manager),
) -> HardwareStatus:
    return manager.get_status()


@router.post("/h4m/import", response_model=H4MImportResult)
def h4m_import(
    request: H4MImportRequest,
    manager: HardwareManager = Depends(get_hardware_manager),
) -> H4MImportResult:
    try:
        return manager.import_h4m(request)
    except HardwareOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
