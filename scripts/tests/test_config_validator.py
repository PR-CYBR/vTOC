from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.lib.config_validator import validate, validate_text

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "inputs.schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_valid_configuration_passes_validation():
    schema = load_schema()
    config = {
        "projectName": "demo",
        "services": {"postgres": True, "traefik": False},
        "cloud": {"provider": "aws", "region": "us-west-2"},
    }

    issues = validate(config, schema)

    assert issues == []


def test_invalid_type_reports_issue():
    schema = load_schema()
    config = {"projectName": 123}

    issues = validate(config, schema)

    assert issues
    assert issues[0].path == "$.projectName"
    assert "Expected type string" in issues[0].message


def test_unexpected_property_reports_issue():
    schema = load_schema()
    config = {"services": {"unknown": True}}

    issues = validate(config, schema)

    assert issues
    assert issues[0].path == "$.services.unknown"
    assert issues[0].message == "Unexpected property"


def test_invalid_enum_reports_issue():
    schema = load_schema()
    config = {"cloud": {"provider": "digitalocean"}}

    issues = validate(config, schema)

    assert issues
    assert issues[0].path == "$.cloud.provider"
    assert "allowed options" in issues[0].message


def test_invalid_json_reports_issue():
    issues = validate_text("{invalid json", SCHEMA_PATH)

    assert issues
    assert issues[0].path == "$"
    assert "Invalid JSON payload" in issues[0].message
