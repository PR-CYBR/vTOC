"""Device management API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .manager import device_manager

router = APIRouter(prefix="/api/v2/rf/devices", tags=["devices"])


class DeviceListResponse(BaseModel):
    """Response model for device list."""

    devices: list[dict[str, Any]] = Field(description="List of detected SDR devices")


class DeviceTestResponse(BaseModel):
    """Response model for device test."""

    device_id: str
    status: str
    error: str | None = None
    message: str | None = None


@router.get("/list", response_model=DeviceListResponse)
def list_devices() -> DeviceListResponse:
    """List all detected SDR devices.

    Returns:
        List of devices with capabilities
    """
    devices = device_manager.list_devices()
    return DeviceListResponse(
        devices=[
            {
                "device_id": d.device_id,
                "driver": d.driver,
                "label": d.label,
                "serial": d.serial,
                "available": d.available,
                "rx_range_mhz": (
                    [d.rx_min_freq_hz / 1e6, d.rx_max_freq_hz / 1e6]
                    if d.rx_min_freq_hz and d.rx_max_freq_hz
                    else None
                ),
                "tx_range_mhz": (
                    [d.tx_min_freq_hz / 1e6, d.tx_max_freq_hz / 1e6]
                    if d.tx_min_freq_hz and d.tx_max_freq_hz
                    else None
                ),
                "sample_rates": d.sample_rates,
                "antennas": d.antennas,
                "error": d.error,
            }
            for d in devices
        ]
    )


@router.post("/{device_id}/test", response_model=DeviceTestResponse)
def test_device(device_id: str) -> DeviceTestResponse:
    """Test device connectivity and basic operation.

    Args:
        device_id: Device identifier (e.g., "rtlsdr-0")

    Returns:
        Test result
    """
    result = device_manager.test_device(device_id)
    return DeviceTestResponse(**result)
