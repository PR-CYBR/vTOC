from __future__ import annotations

from datetime import datetime

import pytest

from backend.app.services.hardware import (
    AdsbConfig,
    AdsbToggleRequest,
    BaseStationConfig,
    BaseStationRegistration,
    GpsTestRequest,
    GpsTestResult,
    HardwareConfiguration,
    HardwareHealthSummary,
    HardwareStatus,
    HardwareOperationError,
    H4MImportRequest,
    H4MImportResult,
    SerialPortInfo,
)
from backend.chatkit.actions.hardware import (
    HardwareActionError,
    h4m_import,
    hw_enable_adsb,
    hw_list_serial,
    hw_register_base_station,
    hw_status,
    hw_test_gps,
)


class FakeHardwareManager:
    def __init__(self) -> None:
        self.serial_ports = [SerialPortInfo(device="/dev/ttyUSB0", description="GPS")]
        self.gps_requests: list[GpsTestRequest] = []
        self.registration_payloads: list[BaseStationRegistration] = []
        self.adsb_payloads: list[AdsbToggleRequest] = []
        self.h4m_payloads: list[H4MImportRequest] = []
        self.status = HardwareStatus(
            configuration=HardwareConfiguration(
                base_station=BaseStationConfig(
                    callsign="TEST", registered_at=datetime.utcnow()
                ),
                adsb=AdsbConfig(
                    enabled=True,
                    device="rtl0",
                    gain=None,
                    frequency=None,
                    options={},
                    last_updated_at=datetime.utcnow(),
                ),
                last_h4m_import_at=datetime.utcnow(),
            ),
            serial_ports=self.serial_ports,
            health=HardwareHealthSummary(
                gps="configured",
                adsb="enabled",
                h4m="imported",
                generated_at=datetime.utcnow(),
            ),
        )
        self.gps_result = GpsTestResult(success=True, command=["gpsctl"], output="ok")
        self.h4m_result = H4MImportResult(
            imported=True, destination="/tmp/h4m", files=["/tmp/h4m/file1"]
        )

    def list_serial_ports(self) -> list[SerialPortInfo]:
        return self.serial_ports

    def test_gps(self, request: GpsTestRequest) -> GpsTestResult:
        self.gps_requests.append(request)
        return self.gps_result

    def register_base_station(
        self, registration: BaseStationRegistration
    ) -> BaseStationConfig:
        self.registration_payloads.append(registration)
        return BaseStationConfig(
            callsign=registration.callsign,
            serial_number=registration.serial_number,
            latitude=registration.latitude,
            longitude=registration.longitude,
            altitude_m=registration.altitude_m,
            notes=registration.notes,
            registered_at=datetime.utcnow(),
        )

    def enable_adsb(self, request: AdsbToggleRequest) -> AdsbConfig:
        self.adsb_payloads.append(request)
        return AdsbConfig(
            enabled=request.enabled,
            device=request.device,
            gain=request.gain,
            frequency=request.frequency,
            options=dict(request.options),
            last_updated_at=datetime.utcnow(),
        )

    def get_status(self) -> HardwareStatus:
        return self.status

    def import_h4m(self, request: H4MImportRequest) -> H4MImportResult:
        self.h4m_payloads.append(request)
        return self.h4m_result


@pytest.fixture(name="anyio_backend")
def anyio_backend_fixture() -> str:
    return "asyncio"


@pytest.mark.anyio("asyncio")
async def test_hw_list_serial_action() -> None:
    manager = FakeHardwareManager()
    result = await hw_list_serial(manager=manager)
    assert result["ports"][0]["device"] == "/dev/ttyUSB0"


@pytest.mark.anyio("asyncio")
async def test_hw_test_gps_action_success() -> None:
    manager = FakeHardwareManager()
    result = await hw_test_gps({"port": "/dev/ttyUSB0"}, manager=manager)
    assert result["success"] is True
    assert manager.gps_requests[0].port == "/dev/ttyUSB0"


@pytest.mark.anyio("asyncio")
async def test_hw_test_gps_action_failure() -> None:
    manager = FakeHardwareManager()
    manager.gps_result = GpsTestResult(success=False, command=["gpsctl"], error="bad")

    with pytest.raises(HardwareActionError):
        await hw_test_gps({"port": "/dev/ttyUSB0"}, manager=manager)


@pytest.mark.anyio("asyncio")
async def test_hw_register_base_station_action() -> None:
    manager = FakeHardwareManager()
    result = await hw_register_base_station({"callsign": "TEST"}, manager=manager)
    assert result["callsign"] == "TEST"
    assert manager.registration_payloads[0].callsign == "TEST"


@pytest.mark.anyio("asyncio")
async def test_hw_enable_adsb_action_handles_error() -> None:
    class ErrorManager(FakeHardwareManager):
        def enable_adsb(self, request: AdsbToggleRequest) -> AdsbConfig:
            raise HardwareOperationError("boom")

    manager = ErrorManager()

    with pytest.raises(HardwareActionError):
        await hw_enable_adsb({"enabled": True}, manager=manager)


@pytest.mark.anyio("asyncio")
async def test_hw_status_action() -> None:
    manager = FakeHardwareManager()
    result = await hw_status(manager=manager)
    assert result["configuration"]["base_station"]["callsign"] == "TEST"


@pytest.mark.anyio("asyncio")
async def test_h4m_import_action() -> None:
    manager = FakeHardwareManager()
    result = await h4m_import({"source_path": "./file.zip"}, manager=manager)
    assert result["imported"] is True
    assert manager.h4m_payloads[0].source_path == "./file.zip"


@pytest.mark.anyio("asyncio")
async def test_h4m_import_action_error() -> None:
    class ErrorManager(FakeHardwareManager):
        def import_h4m(self, request: H4MImportRequest) -> H4MImportResult:
            raise HardwareOperationError("fail")

    manager = ErrorManager()

    with pytest.raises(HardwareActionError):
        await h4m_import({"source_path": "./file.zip"}, manager=manager)
