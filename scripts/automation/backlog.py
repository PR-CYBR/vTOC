"""Utilities for managing Codex backlog entries."""
from __future__ import annotations

import argparse
import json
import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

ID_PREFIX = "codex-"
ID_PADDING = 4
DEFAULT_FILE = Path("codex/backlog.json")


class BacklogError(Exception):
    """Raised when the backlog file is invalid."""


def _normalize_text(value: str) -> str:
    """Normalize multiline text for storage."""
    dedented = textwrap.dedent(value)
    lines = [line.rstrip() for line in dedented.splitlines()]
    normalized = "\n".join(lines).strip()
    return normalized


def _load_entries(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return _ensure_entries(data, require_sorted=False)


def _ensure_entries(data: Any, *, require_sorted: bool) -> List[Dict[str, Any]]:
    if not isinstance(data, list):
        raise BacklogError("Backlog file must contain a JSON array")
    entries: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    previous_key: int | None = None
    for raw in data:
        if not isinstance(raw, dict):
            raise BacklogError("Each backlog entry must be a JSON object")
        entry = dict(raw)
        entry_id = entry.get("id")
        if not isinstance(entry_id, str):
            raise BacklogError("Backlog entries must include a string 'id'")
        key = _id_sort_key(entry_id)
        if entry_id in seen_ids:
            raise BacklogError(f"Duplicate backlog id detected: {entry_id}")
        seen_ids.add(entry_id)
        if require_sorted and previous_key is not None and key < previous_key:
            raise BacklogError("Backlog entries must be sorted by id")
        previous_key = key

        title = entry.get("title")
        summary = entry.get("summary")
        metadata = entry.get("metadata", {})
        created_at = entry.get("created_at")
        if not isinstance(title, str) or not title.strip():
            raise BacklogError(f"Entry {entry_id} must include a non-empty title")
        if not isinstance(summary, str) or not summary.strip():
            raise BacklogError(f"Entry {entry_id} must include a non-empty summary")
        if not isinstance(metadata, dict):
            raise BacklogError(f"Entry {entry_id} metadata must be an object")
        if created_at is not None and not isinstance(created_at, str):
            raise BacklogError(f"Entry {entry_id} created_at must be a string if provided")
        entries.append(
            {
                "id": entry_id,
                "title": title,
                "summary": summary,
                "metadata": metadata,
                "created_at": created_at,
            }
        )
    return entries


def _id_sort_key(identifier: str) -> int:
    match = re.fullmatch(rf"{re.escape(ID_PREFIX)}(\d+)", identifier)
    if not match:
        raise BacklogError(
            f"Backlog id '{identifier}' must match pattern {ID_PREFIX}<number>"
        )
    return int(match.group(1))


def _write_entries(path: Path, entries: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = list(entries)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _next_id(entries: Iterable[Dict[str, Any]]) -> str:
    max_value = 0
    for entry in entries:
        key = _id_sort_key(entry["id"])
        if key > max_value:
            max_value = key
    return f"{ID_PREFIX}{max_value + 1:0{ID_PADDING}d}"


def cmd_add(args: argparse.Namespace) -> None:
    path = Path(args.file)
    entries = _load_entries(path)
    metadata_raw = args.metadata or ""
    metadata_raw = metadata_raw.strip()
    if metadata_raw:
        try:
            metadata = json.loads(metadata_raw)
        except json.JSONDecodeError as exc:
            raise BacklogError(f"Invalid metadata JSON: {exc}") from exc
        if not isinstance(metadata, dict):
            raise BacklogError("Metadata must decode to an object")
    else:
        metadata = {}
    entry_id = _next_id(entries)
    title = _normalize_text(args.title)
    summary = _normalize_text(args.summary)
    if not title:
        raise BacklogError("Title cannot be empty after normalization")
    if not summary:
        raise BacklogError("Summary cannot be empty after normalization")

    new_entry = {
        "id": entry_id,
        "title": title,
        "summary": summary,
        "metadata": metadata,
        "created_at": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }
    entries.append(new_entry)
    _write_entries(path, entries)
    if args.github_output:
        output_path = Path(args.github_output)
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(f"id={entry_id}\n")
    print(f"Added backlog entry {entry_id}")


def cmd_format(args: argparse.Namespace) -> None:
    path = Path(args.file)
    entries = _load_entries(path)
    sorted_entries = sorted(entries, key=lambda entry: _id_sort_key(entry["id"]))
    _write_entries(path, sorted_entries)
    print(f"Formatted backlog file with {len(sorted_entries)} entries")


def cmd_validate(args: argparse.Namespace) -> None:
    path = Path(args.file)
    entries = _load_entries(path)
    _ensure_entries(entries, require_sorted=True)
    print(f"Validated backlog file with {len(entries)} entries")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Codex backlog entries")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Append a backlog entry")
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--summary", required=True)
    add_parser.add_argument("--metadata", default="")
    add_parser.add_argument("--file", default=str(DEFAULT_FILE))
    add_parser.add_argument("--github-output")
    add_parser.set_defaults(func=cmd_add)

    format_parser = subparsers.add_parser(
        "format", help="Sort and reformat the backlog file"
    )
    format_parser.add_argument("--file", default=str(DEFAULT_FILE))
    format_parser.set_defaults(func=cmd_format)

    validate_parser = subparsers.add_parser(
        "validate", help="Validate backlog schema and ordering"
    )
    validate_parser.add_argument("--file", default=str(DEFAULT_FILE))
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except BacklogError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
