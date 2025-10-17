from __future__ import annotations

from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, Iterable, List

import pytest

from backend.app.services.hardware import (
    AdsbConfig,
    AdsbToggleRequest,
    GpsTestRequest,
    HardwareConfigStore,
    HardwareConfiguration,
    HardwareManager,
    HardwareOperationError,
    HardwareStatus,
    H4MImportRequest,
    SerialPortInfo,
)


class MemoryConfigStore(HardwareConfigStore):
    def __init__(self) -> None:
        self._config = HardwareConfiguration()
        self._path = Path("/tmp/vtoc-hardware-test.json")

    @property
    def path(self) -> Path:  # type: ignore[override]
        return self._path

    def load(self) -> HardwareConfiguration:  # type: ignore[override]
        return self._config

    def save(self, config: HardwareConfiguration) -> HardwareConfiguration:  # type: ignore[override]
        self._config = config
        return config


class FakePort:
    def __init__(self, device: str, description: str, hwid: str) -> None:
        self.device = device
        self.description = description
        self.hwid = hwid


def test_list_serial_ports_uses_provider() -> None:
    calls: List[str] = []

    def provider() -> Iterable[FakePort]:
        calls.append("called")
        return [FakePort("/dev/ttyUSB0", "GPS", "ABC123")]

    manager = HardwareManager(
        config_store=MemoryConfigStore(),
        serial_provider=provider,
    )

    ports = manager.list_serial_ports()

    assert calls == ["called"]
    assert ports[0].device == "/dev/ttyUSB0"


def test_test_gps_runs_process_runner_success() -> None:
    executed: List[List[str]] = []

    def runner(command: List[str], timeout: float | None) -> CompletedProcess[str]:
        executed.append(command)
        return CompletedProcess(command, 0, stdout="lock", stderr="")

    manager = HardwareManager(
        config_store=MemoryConfigStore(),
        serial_provider=lambda: [],
        process_runner=runner,
    )

    result = manager.test_gps(GpsTestRequest(port="/dev/ttyUSB0"))

    assert executed[0][0] == "gpsctl"
    assert result.success is True
    assert result.output == "lock"


def test_test_gps_handles_failure() -> None:
    def runner(command: List[str], timeout: float | None) -> CompletedProcess[str]:
        raise HardwareOperationError("boom")

    manager = HardwareManager(
        config_store=MemoryConfigStore(),
        serial_provider=lambda: [],
        process_runner=runner,
    )

    result = manager.test_gps(GpsTestRequest(port="/dev/ttyUSB1"))

    assert result.success is False
    assert "boom" in (result.error or "")


def test_enable_adsb_runs_command_and_updates_config() -> None:
    executed: List[List[str]] = []

    def runner(command: List[str], timeout: float | None) -> CompletedProcess[str]:
        executed.append(command)
        return CompletedProcess(command, 0, stdout="", stderr="")

    store = MemoryConfigStore()
    manager = HardwareManager(
        config_store=store,
        serial_provider=lambda: [],
        process_runner=runner,
    )

    request = AdsbToggleRequest(enabled=True, device="rtl0", start_command=["rtl_adsb"])
    config = manager.enable_adsb(request)

    assert executed == [["rtl_adsb"]]
    assert config.enabled is True
    assert store.load().adsb.enabled is True


def test_enable_adsb_propagates_errors() -> None:
    def runner(command: List[str], timeout: float | None) -> CompletedProcess[str]:
        raise HardwareOperationError("failure")

    manager = HardwareManager(
        config_store=MemoryConfigStore(),
        serial_provider=lambda: [],
        process_runner=runner,
    )

    request = AdsbToggleRequest(enabled=True, start_command=["rtl_adsb"])

    with pytest.raises(HardwareOperationError):
        manager.enable_adsb(request)


def test_import_h4m_uses_importer_and_updates_timestamp(tmp_path: Path) -> None:
    calls: List[tuple[Path, Path, bool]] = []

    def importer(source: Path, destination: Path, extract: bool) -> dict[str, Any]:
        calls.append((source, destination, extract))
        destination.mkdir(parents=True, exist_ok=True)
        file_path = destination / "file.txt"
        file_path.write_text("data")
        return {"destination": str(destination), "files": [str(file_path)]}

    store = MemoryConfigStore()
    manager = HardwareManager(
        config_store=store,
        serial_provider=lambda: [],
        h4m_importer=importer,
    )

    request = H4MImportRequest(
        source_path=str(tmp_path / "archive.zip"),
        destination_dir=str(tmp_path / "target"),
        extract=False,
    )
    result = manager.import_h4m(request)

    assert calls[0][0].name == "archive.zip"
    assert result.imported is True
    assert store.load().last_h4m_import_at is not None


def test_get_status_aggregates_config() -> None:
    store = MemoryConfigStore()
    configuration = HardwareConfiguration()
    configuration.base_station = None
    configuration.adsb = AdsbConfig(
        enabled=False,
        device=None,
        gain=None,
        frequency=None,
        options={},
        last_updated_at=datetime.utcnow(),
    )
    store.save(configuration)

    manager = HardwareManager(
        config_store=store,
        serial_provider=lambda: [SerialPortInfo(device="/dev/ttyS0")],
    )

    status = manager.get_status()

    assert isinstance(status, HardwareStatus)
    assert status.health.gps == "unconfigured"
    assert status.health.details["serial_ports"] == 1
