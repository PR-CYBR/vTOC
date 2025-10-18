"""Minimal JSON schema validator for setup configuration."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Sequence


@dataclass
class ValidationIssue:
    """Represents a validation problem for a configuration payload."""

    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "message": self.message}


_TYPE_MAP = {
    "object": dict,
    "string": str,
    "boolean": bool,
}


def _type_matches(instance: Any, expected: str) -> bool:
    python_type = _TYPE_MAP.get(expected)
    if python_type is None:
        # Unknown type specifier; treat as a pass so that new schema types
        # added in the future do not break validation unexpectedly.
        return True
    return isinstance(instance, python_type)


def _format_path(path: Sequence[str]) -> str:
    if not path:
        return "$"
    return "$." + ".".join(path)


def _validate(instance: Any, schema: dict[str, Any], path: Sequence[str], issues: List[ValidationIssue]) -> None:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        if not any(_type_matches(instance, t) for t in schema_type):
            issues.append(
                ValidationIssue(
                    path=_format_path(path),
                    message=f"Expected value to match one of types {schema_type}, got {type(instance).__name__}",
                )
            )
            return
    elif isinstance(schema_type, str):
        if not _type_matches(instance, schema_type):
            issues.append(
                ValidationIssue(
                    path=_format_path(path),
                    message=f"Expected type {schema_type}, got {type(instance).__name__}",
                )
            )
            return

    enum_values = schema.get("enum")
    if enum_values is not None and instance not in enum_values:
        issues.append(
            ValidationIssue(
                path=_format_path(path),
                message=f"Value {instance!r} is not one of the allowed options: {enum_values}",
            )
        )
        return

    if schema_type == "object" and isinstance(instance, dict):
        properties: dict[str, Any] = schema.get("properties", {})
        required: Iterable[str] = schema.get("required", [])

        for required_key in required:
            if required_key not in instance:
                issues.append(
                    ValidationIssue(
                        path=_format_path([*path, required_key]),
                        message="Missing required property",
                    )
                )

        additional_allowed = schema.get("additionalProperties", True)
        for key, value in instance.items():
            next_path = [*path, key]
            if key in properties:
                _validate(value, properties[key], next_path, issues)
            elif additional_allowed is False:
                issues.append(
                    ValidationIssue(
                        path=_format_path(next_path),
                        message="Unexpected property",
                    )
                )


def validate(instance: Any, schema: dict[str, Any]) -> list[ValidationIssue]:
    """Validate *instance* against *schema* and return any issues found."""

    issues: list[ValidationIssue] = []
    _validate(instance, schema, (), issues)
    return issues


def _load_json(data: str) -> Any:
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Invalid JSON payload: {exc.msg}") from exc


def _load_schema(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Schema file not found: {path}") from exc


def validate_text(config_text: str, schema_path: Path) -> list[ValidationIssue]:
    schema = _load_schema(schema_path)
    try:
        instance = _load_json(config_text or "{}")
    except ValueError as exc:
        return [ValidationIssue(path="$", message=str(exc))]
    return validate(instance, schema)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate setup configuration payloads")
    parser.add_argument("schema", type=Path, help="Path to the JSON schema file")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to the JSON configuration file. If omitted, stdin is used.",
    )
    args = parser.parse_args()

    if args.config is not None:
        config_text = args.config.read_text(encoding="utf-8")
    else:
        config_text = sys.stdin.read()

    try:
        issues = validate_text(config_text, args.schema)
    except ValueError as exc:
        print(json.dumps({"path": "$", "message": str(exc)}), file=sys.stderr)
        return 1
    if issues:
        for issue in issues:
            print(json.dumps(issue.to_dict()), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
