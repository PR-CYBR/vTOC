from __future__ import annotations

from datetime import datetime
from typing import List

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.hardware import (
    AdsbConfig,
    AdsbToggleRequest,
    BaseStationConfig,
    BaseStationRegistration,
    GpsTestRequest,
    GpsTestResult,
    H4MImportRequest,
    H4MImportResult,
    HardwareConfiguration,
    HardwareHealthSummary,
    HardwareManager,
    HardwareOperationError,
    HardwareStatus,
    SerialPortInfo,
    get_hardware_manager,
)


class DummyHardwareManager(HardwareManager):
    def __init__(self) -> None:
        super().__init__(serial_provider=lambda: [])
        self.list_called = False
        self.gps_requests: List[GpsTestRequest] = []
        self.registration_payloads: List[BaseStationRegistration] = []
        self.adsb_requests: List[AdsbToggleRequest] = []
        self.h4m_requests: List[H4MImportRequest] = []

    def list_serial_ports(self) -> List[SerialPortInfo]:
        self.list_called = True
        return [
            SerialPortInfo(device="/dev/ttyUSB0", description="GPS", hwid="ABC123"),
            SerialPortInfo(device="/dev/ttyUSB1", description="ADS-B", hwid="XYZ789"),
        ]

    def test_gps(self, request: GpsTestRequest) -> GpsTestResult:
        self.gps_requests.append(request)
        return GpsTestResult(success=True, command=["gpsctl"], output="ok")

    def register_base_station(self, registration: BaseStationRegistration) -> BaseStationConfig:
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
        self.adsb_requests.append(request)
        return AdsbConfig(
            enabled=request.enabled,
            device=request.device,
            gain=request.gain,
            frequency=request.frequency,
            options=dict(request.options),
            last_updated_at=datetime.utcnow(),
        )

    def get_status(self) -> HardwareStatus:
        configuration = HardwareConfiguration(
            base_station=BaseStationConfig(
                callsign="STATION", registered_at=datetime.utcnow()
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
        )
        ports = self.list_serial_ports()
        health = HardwareHealthSummary(
            gps="configured",
            adsb="enabled",
            h4m="imported",
            generated_at=datetime.utcnow(),
            details={"serial_ports": len(ports)},
        )
        return HardwareStatus(
            configuration=configuration,
            serial_ports=ports,
            health=health,
        )

    def import_h4m(self, request: H4MImportRequest) -> H4MImportResult:
        self.h4m_requests.append(request)
        return H4MImportResult(
            imported=True,
            destination="/tmp/h4m",
            files=["/tmp/h4m/file1.json"],
        )


@pytest.fixture()
def dummy_manager() -> DummyHardwareManager:
    return DummyHardwareManager()


@pytest.fixture()
def client(dummy_manager: DummyHardwareManager) -> TestClient:
    test_client = TestClient(app)
    app.dependency_overrides[get_hardware_manager] = lambda: dummy_manager
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_hardware_manager, None)
        test_client.close()


def test_hw_list_serial(client: TestClient, dummy_manager: DummyHardwareManager) -> None:
    response = client.get("/api/v1/hardware/serial")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert dummy_manager.list_called
    assert payload[0]["device"] == "/dev/ttyUSB0"


def test_hw_test_gps(client: TestClient, dummy_manager: DummyHardwareManager) -> None:
    response = client.post(
        "/api/v1/hardware/test-gps",
        json={"port": "/dev/ttyUSB0", "baudrate": 4800},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert dummy_manager.gps_requests[0].port == "/dev/ttyUSB0"


def test_hw_register_base_station(client: TestClient, dummy_manager: DummyHardwareManager) -> None:
    response = client.post(
        "/api/v1/hardware/register-base-station",
        json={
            "callsign": "STATION",
            "serial_number": "SN123",
            "latitude": 40.0,
            "longitude": -75.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["callsign"] == "STATION"
    assert dummy_manager.registration_payloads[0].callsign == "STATION"


def test_hw_enable_adsb(client: TestClient, dummy_manager: DummyHardwareManager) -> None:
    response = client.post(
        "/api/v1/hardware/enable-adsb",
        json={"enabled": True, "device": "rtl0", "start_command": ["rtl_adsb"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert dummy_manager.adsb_requests[0].device == "rtl0"


def test_hw_status(client: TestClient) -> None:
    response = client.get("/api/v1/hardware/status")
    assert response.status_code == 200
    data = response.json()
    assert data["health"]["adsb"] == "enabled"
    assert data["configuration"]["base_station"]["callsign"] == "STATION"


def test_h4m_import(client: TestClient, dummy_manager: DummyHardwareManager) -> None:
    response = client.post(
        "/api/v1/hardware/h4m/import",
        json={"source_path": "./data.h4m", "destination_dir": "./output"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imported"] is True
    assert dummy_manager.h4m_requests[0].source_path == "./data.h4m"


def test_hw_register_base_station_error(client: TestClient, dummy_manager: DummyHardwareManager) -> None:
    def _raise(_: BaseStationRegistration) -> BaseStationConfig:
        raise HardwareOperationError("failed")

    dummy_manager.register_base_station = _raise  # type: ignore[assignment]

    response = client.post(
        "/api/v1/hardware/register-base-station",
        json={"callsign": "BAD"},
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "failed"
