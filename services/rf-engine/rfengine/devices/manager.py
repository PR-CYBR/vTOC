"""Device management module for RF Engine.

Provides SoapySDR-based abstraction for multi-vendor SDR devices.
Clean-room implementation (no FISSURE code copied).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger

from ..config import settings


@dataclass
class DeviceInfo:
    """SDR device information."""

    device_id: str
    driver: str
    label: str
    serial: str | None
    available: bool
    rx_min_freq_hz: float | None = None
    rx_max_freq_hz: float | None = None
    tx_min_freq_hz: float | None = None
    tx_max_freq_hz: float | None = None
    sample_rates: list[float] | None = None
    antennas: list[str] | None = None
    error: str | None = None


class DeviceManager:
    """Manages SDR device discovery and access via SoapySDR.

    This is a placeholder implementation that provides the API structure.
    Full SoapySDR integration requires GNU Radio/SoapySDR libraries installed.
    """

    def __init__(self):
        """Initialize device manager."""
        self._soapy_available = False
        self._check_soapy()

    def _check_soapy(self) -> None:
        """Check if SoapySDR is available."""
        try:
            import SoapySDR  # noqa: F401

            self._soapy_available = True
            logger.info("SoapySDR available")
        except ImportError:
            logger.warning(
                "SoapySDR not available - device management will be limited. "
                "Install SoapySDR for full functionality."
            )
            self._soapy_available = False

    def list_devices(self) -> list[DeviceInfo]:
        """List all detected SDR devices.

        Returns:
            List of device information
        """
        if not self._soapy_available:
            logger.warning("SoapySDR not available - returning mock device")
            return [
                DeviceInfo(
                    device_id="mock-rtl-0",
                    driver="rtlsdr",
                    label="Mock RTL-SDR (SoapySDR not installed)",
                    serial=None,
                    available=False,
                    error="SoapySDR not installed",
                )
            ]

        try:
            import SoapySDR

            devices = []
            results = SoapySDR.Device.enumerate()

            for i, result in enumerate(results):
                driver = result.get("driver", "unknown")

                # Check if driver is in allowlist
                if driver not in settings.allowed_devices:
                    logger.debug(f"Skipping device {driver} (not in allowlist)")
                    continue

                device_info = DeviceInfo(
                    device_id=f"{driver}-{i}",
                    driver=driver,
                    label=result.get("label", f"{driver} #{i}"),
                    serial=result.get("serial", None),
                    available=True,
                )

                # Try to get device capabilities
                try:
                    device = SoapySDR.Device(result)
                    
                    # Get RX frequency range
                    if device.listAntennas(SoapySDR.SOAPY_SDR_RX, 0):
                        rx_range = device.getFrequencyRange(SoapySDR.SOAPY_SDR_RX, 0)
                        if rx_range:
                            device_info.rx_min_freq_hz = rx_range[0].minimum()
                            device_info.rx_max_freq_hz = rx_range[0].maximum()

                    # Get TX frequency range (if TX capable)
                    if device.listAntennas(SoapySDR.SOAPY_SDR_TX, 0):
                        tx_range = device.getFrequencyRange(SoapySDR.SOAPY_SDR_TX, 0)
                        if tx_range:
                            device_info.tx_min_freq_hz = tx_range[0].minimum()
                            device_info.tx_max_freq_hz = tx_range[0].maximum()

                    # Get sample rates
                    rates = device.listSampleRates(SoapySDR.SOAPY_SDR_RX, 0)
                    device_info.sample_rates = rates

                    # Get antennas
                    antennas = device.listAntennas(SoapySDR.SOAPY_SDR_RX, 0)
                    device_info.antennas = antennas

                    device.unmake()
                except Exception as e:
                    logger.warning(f"Failed to probe device {device_info.device_id}: {e}")
                    device_info.error = str(e)

                devices.append(device_info)

            logger.info(f"Found {len(devices)} allowed SDR devices")
            return devices

        except Exception as e:
            logger.error(f"Failed to enumerate devices: {e}")
            return []

    def test_device(self, device_id: str) -> dict[str, Any]:
        """Test device connectivity and basic operation.

        Args:
            device_id: Device identifier

        Returns:
            Test results
        """
        if not self._soapy_available:
            return {
                "device_id": device_id,
                "status": "error",
                "error": "SoapySDR not installed",
            }

        try:
            import SoapySDR

            # Parse device_id (format: driver-index)
            parts = device_id.split("-")
            if len(parts) < 2:
                return {
                    "device_id": device_id,
                    "status": "error",
                    "error": "Invalid device_id format",
                }

            driver = parts[0]
            index = int(parts[1])

            # Enumerate to find device
            results = SoapySDR.Device.enumerate()
            if index >= len(results):
                return {
                    "device_id": device_id,
                    "status": "error",
                    "error": "Device index out of range",
                }

            result = results[index]
            if result.get("driver") != driver:
                return {
                    "device_id": device_id,
                    "status": "error",
                    "error": "Driver mismatch",
                }

            # Try to open device
            device = SoapySDR.Device(result)
            device.unmake()

            return {
                "device_id": device_id,
                "status": "ok",
                "message": "Device test successful",
            }

        except Exception as e:
            logger.error(f"Device test failed for {device_id}: {e}")
            return {
                "device_id": device_id,
                "status": "error",
                "error": str(e),
            }


# Global device manager instance
device_manager = DeviceManager()
