"""Hardware orchestration helpers."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Sequence

from pydantic import BaseModel, Field, ConfigDict


class HardwareOperationError(RuntimeError):
    """Raised when an operation interacting with hardware fails."""


class SerialPortInfo(BaseModel):
    """Description of a serial port reported by the system."""

    model_config = ConfigDict(extra="forbid")

    device: str
    description: Optional[str] = None
    hwid: Optional[str] = None


class GpsTestRequest(BaseModel):
    """Input payload used to run a GPS self-test."""

    model_config = ConfigDict(extra="forbid")

    port: str
    baudrate: int = Field(default=9600, ge=1)
    timeout_seconds: float = Field(default=5.0, ge=0.1)


class GpsTestResult(BaseModel):
    """Result payload returned by :meth:`HardwareManager.test_gps`."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    command: List[str]
    output: Optional[str] = None
    error: Optional[str] = None


class BaseStationRegistration(BaseModel):
    """Information required to persist a base station registration."""

    model_config = ConfigDict(extra="forbid")

    callsign: str
    serial_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    notes: Optional[str] = None


class BaseStationConfig(BaseModel):
    """Stored base station configuration."""

    model_config = ConfigDict(extra="forbid")

    callsign: str
    serial_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    notes: Optional[str] = None
    registered_at: datetime


class AdsbToggleRequest(BaseModel):
    """Request payload for toggling ADS-B capture."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    device: Optional[str] = None
    gain: Optional[float] = None
    frequency: Optional[float] = None
    options: dict[str, Any] = Field(default_factory=dict)
    start_command: Optional[List[str]] = None
    stop_command: Optional[List[str]] = None
    timeout_seconds: Optional[float] = Field(default=10.0, ge=0.1)


class AdsbConfig(BaseModel):
    """Persisted ADS-B configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    device: Optional[str] = None
    gain: Optional[float] = None
    frequency: Optional[float] = None
    options: dict[str, Any] = Field(default_factory=dict)
    last_updated_at: datetime


class H4MImportRequest(BaseModel):
    """Request payload for importing H4M datasets."""

    model_config = ConfigDict(extra="forbid")

    source_path: str
    destination_dir: Optional[str] = None
    extract: bool = True


class H4MImportResult(BaseModel):
    """Result payload returned after importing an H4M archive."""

    model_config = ConfigDict(extra="forbid")

    imported: bool
    destination: str
    files: List[str] = Field(default_factory=list)


class HardwareHealthSummary(BaseModel):
    """Aggregated health signals for hardware subsystems."""

    model_config = ConfigDict(extra="forbid")

    gps: str
    adsb: str
    h4m: str
    generated_at: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class HardwareConfiguration(BaseModel):
    """Root configuration container persisted to disk."""

    model_config = ConfigDict(extra="forbid")

    base_station: Optional[BaseStationConfig] = None
    adsb: Optional[AdsbConfig] = None
    last_h4m_import_at: Optional[datetime] = None


class HardwareStatus(BaseModel):
    """Combined view of configuration, connected devices, and health."""

    model_config = ConfigDict(extra="forbid")

    configuration: HardwareConfiguration
    serial_ports: List[SerialPortInfo]
    health: HardwareHealthSummary


class HardwareConfigStore:
    """Persist and retrieve :class:`HardwareConfiguration` instances."""

    def __init__(self, path: Optional[Path] = None) -> None:
        default_path = (
            Path(os.getenv("VTOC_HARDWARE_CONFIG", "~/.config/vtoc/hardware.json"))
            .expanduser()
            .resolve()
        )
        self._path = path.resolve() if path is not None else default_path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> HardwareConfiguration:
        if not self._path.exists():
            return HardwareConfiguration()
        try:
            raw = self._path.read_text(encoding="utf-8").strip()
        except OSError as exc:  # pragma: no cover - disk error
            raise HardwareOperationError(f"Failed to read hardware configuration: {exc}") from exc
        if not raw:
            return HardwareConfiguration()
        try:
            payload = json.loads(raw)
            return HardwareConfiguration.model_validate(payload)
        except Exception as exc:  # pragma: no cover - invalid file contents
            raise HardwareOperationError("Hardware configuration file is corrupt") from exc

    def save(self, config: HardwareConfiguration) -> HardwareConfiguration:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                config.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
            )
        except OSError as exc:  # pragma: no cover - disk error
            raise HardwareOperationError(f"Failed to write hardware configuration: {exc}") from exc
        return config


ProcessRunner = Callable[[Sequence[str], Optional[float]], subprocess.CompletedProcess[str]]
H4MImporter = Callable[[Path, Path, bool], dict[str, Any]]
SerialPortProvider = Callable[[], Iterable[Any]]


@dataclass
class HardwareManager:
    """Coordinate interactions with station-attached hardware."""

    config_store: HardwareConfigStore = field(default_factory=HardwareConfigStore)
    serial_provider: SerialPortProvider | None = None
    process_runner: ProcessRunner | None = None
    h4m_importer: H4MImporter | None = None

    def __post_init__(self) -> None:
        self._config: Optional[HardwareConfiguration] = None
        if self.serial_provider is None:
            self.serial_provider = self._default_serial_provider
        if self.process_runner is None:
            self.process_runner = self._default_process_runner
        if self.h4m_importer is None:
            self.h4m_importer = self._default_h4m_importer

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_config(self) -> HardwareConfiguration:
        if self._config is None:
            self._config = self.config_store.load()
        return self._config

    def _save_config(self, config: HardwareConfiguration) -> HardwareConfiguration:
        saved = self.config_store.save(config)
        self._config = saved
        return saved

    def _default_serial_provider(self) -> Iterable[Any]:
        try:  # pragma: no cover - pyserial may be missing in CI
            from serial.tools import list_ports
        except Exception:
            return []
        return list_ports.comports()

    def _default_process_runner(
        self, command: Sequence[str], timeout: Optional[float]
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                list(command),
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout,
            )
        except subprocess.CalledProcessError as exc:
            output = exc.stdout or exc.stderr or str(exc)
            raise HardwareOperationError(
                f"Command failed: {' '.join(command)}: {output.strip()}"
            ) from exc

    def _default_h4m_importer(self, source: Path, destination: Path, extract: bool) -> dict[str, Any]:
        if not source.exists():
            raise HardwareOperationError(f"H4M archive not found: {source}")
        destination.mkdir(parents=True, exist_ok=True)
        files: list[str] = []
        target: Path
        if extract and shutil.which("unzip") and source.suffix.lower() in {".zip", ".kmz"}:
            # Attempt to unpack archives commonly used for airspace datasets.
            target = destination / source.stem
            target.mkdir(parents=True, exist_ok=True)
            shutil.unpack_archive(str(source), str(target))
            for item in target.rglob("*"):
                if item.is_file():
                    files.append(str(item))
        else:
            target = destination / source.name
            shutil.copy2(source, target)
            files.append(str(target))
        return {"destination": str(target), "files": files}

    def _run_command(self, command: Sequence[str], timeout: Optional[float]) -> subprocess.CompletedProcess[str]:
        assert self.process_runner is not None  # for mypy
        return self.process_runner(command, timeout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_serial_ports(self) -> List[SerialPortInfo]:
        assert self.serial_provider is not None  # for mypy
        ports: List[SerialPortInfo] = []
        for port in self.serial_provider():
            device = getattr(port, "device", None) or getattr(port, "name", None)
            if not device:
                continue
            info = SerialPortInfo(
                device=device,
                description=getattr(port, "description", None),
                hwid=getattr(port, "hwid", None),
            )
            ports.append(info)
        return ports

    def test_gps(self, request: GpsTestRequest) -> GpsTestResult:
        command = [
            "gpsctl",
            "--device",
            request.port,
            "--baud",
            str(request.baudrate),
        ]
        try:
            completed = self._run_command(command, timeout=request.timeout_seconds)
            output = (completed.stdout or "").strip()
            return GpsTestResult(success=True, command=list(command), output=output)
        except HardwareOperationError as exc:
            return GpsTestResult(
                success=False,
                command=list(command),
                error=str(exc),
            )

    def register_base_station(self, registration: BaseStationRegistration) -> BaseStationConfig:
        config = self._get_config()
        stored = BaseStationConfig(
            callsign=registration.callsign,
            serial_number=registration.serial_number,
            latitude=registration.latitude,
            longitude=registration.longitude,
            altitude_m=registration.altitude_m,
            notes=registration.notes,
            registered_at=datetime.utcnow(),
        )
        config.base_station = stored
        self._save_config(config)
        return stored

    def enable_adsb(self, request: AdsbToggleRequest) -> AdsbConfig:
        config = self._get_config()
        adsb_config = AdsbConfig(
            enabled=request.enabled,
            device=request.device,
            gain=request.gain,
            frequency=request.frequency,
            options=dict(request.options),
            last_updated_at=datetime.utcnow(),
        )
        timeout = request.timeout_seconds
        command = request.start_command if request.enabled else request.stop_command
        if command:
            self._run_command(command, timeout=timeout)
        config.adsb = adsb_config
        self._save_config(config)
        return adsb_config

    def get_status(self) -> HardwareStatus:
        config = self._get_config()
        ports = self.list_serial_ports()
        health = HardwareHealthSummary(
            gps="configured" if config.base_station else "unconfigured",
            adsb="enabled" if config.adsb and config.adsb.enabled else "disabled",
            h4m="imported" if config.last_h4m_import_at else "missing",
            generated_at=datetime.utcnow(),
            details={
                "serial_ports": len(ports),
                "adsb_device": config.adsb.device if config.adsb else None,
            },
        )
        return HardwareStatus(configuration=config, serial_ports=ports, health=health)

    def import_h4m(self, request: H4MImportRequest) -> H4MImportResult:
        source = Path(request.source_path).expanduser().resolve()
        destination = (
            Path(request.destination_dir).expanduser().resolve()
            if request.destination_dir
            else self.config_store.path.parent / "h4m"
        )
        importer = self.h4m_importer
        assert importer is not None  # for mypy
        try:
            result = importer(source, destination, request.extract)
        except HardwareOperationError:
            raise
        except Exception as exc:  # pragma: no cover - unexpected importer failure
            raise HardwareOperationError(f"Failed to import H4M archive: {exc}") from exc
        config = self._get_config()
        config.last_h4m_import_at = datetime.utcnow()
        self._save_config(config)
        return H4MImportResult(
            imported=True,
            destination=result.get("destination", str(destination)),
            files=result.get("files", []),
        )


def get_hardware_manager() -> HardwareManager:
    """FastAPI dependency that returns a :class:`HardwareManager`."""

    return HardwareManager()
