"""RF Engine configuration using Pydantic Settings.

All configuration values loaded from environment variables with PRCYBR_/RF_ prefixes.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RFEngineSettings(BaseSettings):
    """RF Engine configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    # Station identity
    prcybr_station_id: str = Field(
        default="vtoc-001", description="Station identifier for telemetry"
    )
    prcybr_division: str = Field(default="DIV-PR-001", description="Division identifier")

    # Device configuration
    rf_devices_allowlist: str = Field(
        default="rtlsdr,usrp,hackrf,limesdr",
        description="Comma-separated list of allowed SDR device types",
    )

    # TX gating and security
    rf_tx_enabled: bool = Field(
        default=False, description="Master switch for transmit capabilities (default: disabled)"
    )
    rf_tx_whitelist_freqs_mhz: str = Field(
        default="",
        description="Comma-separated list of allowed TX center frequencies in MHz (empty = none allowed)",
    )

    # Storage configuration
    rf_sigmf_root: str = Field(
        default="/data/sigmf", description="Local filesystem root for SigMF captures"
    )
    rf_s3_endpoint: str = Field(
        default="http://minio:9000", description="S3-compatible storage endpoint"
    )
    rf_s3_bucket: str = Field(default="prcybr-rf", description="S3 bucket for RF archives")
    rf_s3_access_key: str = Field(default="prcybr_rf_access", description="S3 access key")
    rf_s3_secret_key: str = Field(default="", description="S3 secret key (never commit!)")

    # Classification
    rf_classifier_model_path: str = Field(
        default="/models/spectro_cnn.onnx", description="Path to ONNX classifier model"
    )

    # WebSocket streaming
    rf_ws_sample_rate_hz: int = Field(
        default=1000000, description="WebSocket stream sample rate (Hz)"
    )
    rf_ws_fft_size: int = Field(default=2048, description="FFT size for PSD streaming")

    # Safety limits
    rf_max_capture_seconds: int = Field(
        default=3600, description="Maximum single capture duration (seconds)"
    )

    # Backend integration
    backend_base_url: str = Field(
        default="http://backend:8080", description="vTOC backend API base URL"
    )

    # Database
    database_url: str = Field(
        default="postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc",
        description="PostgreSQL connection string",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="info", description="Logging level")

    @property
    def allowed_devices(self) -> list[str]:
        """Parse allowlist into list of device types."""
        return [d.strip() for d in self.rf_devices_allowlist.split(",") if d.strip()]

    @property
    def tx_whitelist_freqs(self) -> list[float]:
        """Parse TX whitelist into list of frequencies in Hz."""
        if not self.rf_tx_whitelist_freqs_mhz:
            return []
        return [
            float(f.strip()) * 1e6
            for f in self.rf_tx_whitelist_freqs_mhz.split(",")
            if f.strip()
        ]

    def is_tx_allowed(self, freq_hz: float) -> bool:
        """Check if TX is allowed at the given frequency.

        Args:
            freq_hz: Frequency in Hz

        Returns:
            True if TX enabled and frequency in whitelist, False otherwise
        """
        if not self.rf_tx_enabled:
            return False
        if not self.tx_whitelist_freqs:
            return False
        # Allow ±1 MHz tolerance
        tolerance = 1e6
        return any(abs(freq_hz - allowed) < tolerance for allowed in self.tx_whitelist_freqs)


# Global settings instance
settings = RFEngineSettings()
