import os
from pathlib import Path

from scripts.configure_readsb import build_values, render
from scripts.configure_readsb import DUMP1090_TEMPLATE, READSB_TEMPLATE


def test_build_values_overrides_env(monkeypatch):
    monkeypatch.setenv("RTL_DEVICE", "1")
    monkeypatch.setenv("RTL_GAIN", "48.0")
    monkeypatch.setenv("RECEIVER_LAT", "51.5")
    monkeypatch.setenv("RECEIVER_LON", "-0.1")
    monkeypatch.setenv("READSB_JSON_DIR", "/tmp/json")

    values = build_values()
    assert values["RTL_DEVICE"] == "1"
    assert values["RTL_GAIN"] == "48.0"
    assert values["JSON_DIR"] == "/tmp/json"
    assert values["RECEIVER_LAT"] == "51.5"


def test_render_readsb_template(tmp_path: Path):
    output = tmp_path / "readsb.conf"
    values = {
        "RTL_DEVICE": "1",
        "RTL_GAIN": "48.0",
        "RTL_PPM": "0",
        "RECEIVER_LAT": "51.5",
        "RECEIVER_LON": "-0.1",
        "JSON_DIR": "/run/readsb",
        "MLAT_PORT": "30104",
        "BEAST_OUTPUT": "30005",
        "RAW_OUTPUT": "30002",
        "MAX_RANGE": "360",
    }
    content = render(READSB_TEMPLATE, values)
    output.write_text(content, encoding="utf-8")
    written = output.read_text(encoding="utf-8")
    assert "--device-index 1" in written
    assert "LAT=51.5" in written


def test_render_dump1090_template(tmp_path: Path):
    values = {
        "RTL_DEVICE": "2",
        "RTL_GAIN": "max",
        "RTL_PPM": "0",
        "RECEIVER_LAT": "40.0",
        "RECEIVER_LON": "-75.0",
        "JSON_DIR": "/run/dump1090",
        "MLAT_PORT": "30104",
        "BEAST_OUTPUT": "30005",
        "RAW_OUTPUT": "30002",
        "MAX_RANGE": "200",
    }
    content = render(DUMP1090_TEMPLATE, values)
    assert "--max-range 200" in content
    assert "LAT=40.0" in content
