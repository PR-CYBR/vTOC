import pytest

from gps_ingest.parser import GPSFix, parse_nmea_sentence


def test_parse_rmc_sentence_returns_fix():
    sentence = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"

    fix = parse_nmea_sentence(sentence)

    assert isinstance(fix, GPSFix)
    assert pytest.approx(fix.latitude, rel=1e-3) == 48.1173
    assert pytest.approx(fix.longitude, rel=1e-3) == 11.5166667
    assert fix.speed_kmh is not None
    assert fix.speed_kmh == pytest.approx(22.4 * 1.852)


def test_parse_gga_sentence_includes_altitude():
    sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"

    fix = parse_nmea_sentence(sentence)

    assert fix is not None
    assert pytest.approx(fix.altitude_m, rel=1e-3) == 545.4


def test_parse_invalid_sentence_returns_none():
    assert parse_nmea_sentence("$GPRMC,invalid*") is None
    assert parse_nmea_sentence("") is None


def test_parse_sentence_without_position_returns_none():
    # VTG sentences contain velocity but no lat/long.
    sentence = "$GPVTG,054.7,T,034.4,M,005.5,N,010.2,K*48"
    assert parse_nmea_sentence(sentence) is None
