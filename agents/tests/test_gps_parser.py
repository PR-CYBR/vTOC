from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.scraper.gps_parser import (  # noqa: E402
    GpsFix,
    load_nmea_file,
    parse_nmea_log,
    parse_nmea_sentence,
)


def test_parse_valid_rmc_sentence() -> None:
    sentence = "$GPRMC,220516,A,5133.82,N,00042.24,W,173.8,231.8,130694,004.2,W*70"
    fix = parse_nmea_sentence(sentence)

    assert isinstance(fix, GpsFix)
    assert round(fix.latitude, 5) == pytest.approx(51.56367, rel=1e-5)
    assert round(fix.longitude, 5) == pytest.approx(-0.70400, rel=1e-5)
    assert fix.speed_knots == pytest.approx(173.8)
    assert fix.course == pytest.approx(231.8)
    assert fix.timestamp == datetime(1994, 6, 13, 22, 5, 16, tzinfo=timezone.utc)


def test_parse_gga_sentence_includes_altitude() -> None:
    sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    fix = parse_nmea_sentence(sentence)

    assert fix.altitude_m == pytest.approx(545.4)
    assert round(fix.latitude, 4) == pytest.approx(48.1173, rel=1e-4)
    assert round(fix.longitude, 4) == pytest.approx(11.5167, rel=1e-4)


def test_parse_nmea_log_filters_invalid_lines() -> None:
    sample_path = Path(__file__).with_name("data").joinpath("sample_nmea.txt")
    fixes = load_nmea_file(sample_path)

    assert len(fixes) == 5
    assert all(isinstance(item, GpsFix) for item in fixes)

    noisy_lines = [
        "$GPRMC,081836,V,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*6C",  # invalid status
        "$GPGGA,092750.000,5321.6802,N,00630.3372,W,0,00,1.03,76.0,M,55.2,M,,*70",  # no fix
    ]
    fixes = parse_nmea_log(noisy_lines)
    assert fixes == []


def test_invalid_checksum_raises() -> None:
    sentence = "$GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*00"
    with pytest.raises(ValueError, match="checksum"):
        parse_nmea_sentence(sentence)
