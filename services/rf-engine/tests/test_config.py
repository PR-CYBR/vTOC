"""Tests for RF Engine configuration."""

import pytest

from rfengine.config import RFEngineSettings


def test_default_settings():
    """Test default configuration values."""
    settings = RFEngineSettings()

    assert settings.prcybr_station_id == "vtoc-001"
    assert settings.prcybr_division == "DIV-PR-001"
    assert settings.rf_tx_enabled is False
    assert settings.rf_devices_allowlist == "rtlsdr,usrp,hackrf,limesdr"
    assert settings.rf_max_capture_seconds == 3600


def test_allowed_devices_parsing():
    """Test device allowlist parsing."""
    settings = RFEngineSettings(rf_devices_allowlist="rtlsdr,hackrf")
    assert settings.allowed_devices == ["rtlsdr", "hackrf"]

    settings = RFEngineSettings(rf_devices_allowlist="rtlsdr, hackrf , usrp")
    assert settings.allowed_devices == ["rtlsdr", "hackrf", "usrp"]

    settings = RFEngineSettings(rf_devices_allowlist="")
    assert settings.allowed_devices == []


def test_tx_whitelist_parsing():
    """Test TX frequency whitelist parsing."""
    settings = RFEngineSettings(rf_tx_whitelist_freqs_mhz="915.0,433.92")
    expected = [915.0e6, 433.92e6]
    assert len(settings.tx_whitelist_freqs) == 2
    assert abs(settings.tx_whitelist_freqs[0] - expected[0]) < 1.0
    assert abs(settings.tx_whitelist_freqs[1] - expected[1]) < 1.0

    settings = RFEngineSettings(rf_tx_whitelist_freqs_mhz="")
    assert settings.tx_whitelist_freqs == []


def test_is_tx_allowed():
    """Test TX gating logic."""
    # TX disabled
    settings = RFEngineSettings(
        rf_tx_enabled=False, rf_tx_whitelist_freqs_mhz="915.0,433.92"
    )
    assert settings.is_tx_allowed(915.0e6) is False
    assert settings.is_tx_allowed(433.92e6) is False

    # TX enabled but empty whitelist
    settings = RFEngineSettings(rf_tx_enabled=True, rf_tx_whitelist_freqs_mhz="")
    assert settings.is_tx_allowed(915.0e6) is False

    # TX enabled with whitelist
    settings = RFEngineSettings(rf_tx_enabled=True, rf_tx_whitelist_freqs_mhz="915.0,433.92")
    assert settings.is_tx_allowed(915.0e6) is True
    assert settings.is_tx_allowed(433.92e6) is True
    assert settings.is_tx_allowed(868.0e6) is False  # Not in whitelist

    # Test tolerance (±1 MHz)
    assert settings.is_tx_allowed(915.5e6) is True  # Within tolerance
    assert settings.is_tx_allowed(916.5e6) is False  # Outside tolerance


def test_tx_default_disabled():
    """Test that TX is disabled by default (security)."""
    settings = RFEngineSettings()
    assert settings.rf_tx_enabled is False
    assert settings.tx_whitelist_freqs == []
    assert settings.is_tx_allowed(915.0e6) is False
