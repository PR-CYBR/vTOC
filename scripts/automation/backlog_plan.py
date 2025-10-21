#!/usr/bin/env python3
"""Generate a Codex plan for a backlog entry and persist it to backlog/backlog.yaml."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency resolution handled by workflow
    raise SystemExit("PyYAML must be installed to use backlog_plan.py") from exc


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ID_PREFIX = "BL-"
ID_PADDING = 3


class BacklogPlanError(Exception):
    """Raised when the backlog registry has an unexpected structure."""


@dataclass
class PlanResult:
    project_item_id: str
    skipped: bool
    entry_id: str | None = None
    plan_url: str | None = None
    tasks: List[Dict[str, Any]] | None = None
    spec_feature: str | None = None
    spec_tasks_path: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "project_item_id": self.project_item_id,
            "skipped": self.skipped,
        }
        if self.entry_id is not None:
            data["entry_id"] = self.entry_id
        if self.plan_url is not None:
            data["plan_url"] = self.plan_url
        if self.tasks is not None:
            data["tasks"] = self.tasks
        if self.spec_feature is not None:
            data["spec_feature"] = self.spec_feature
        if self.spec_tasks_path is not None:
            data["spec_tasks_path"] = self.spec_tasks_path
        return data


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_backlog(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except OSError as exc:  # pragma: no cover - hard to simulate reliably
        raise BacklogPlanError(f"Failed to read backlog file {path}: {exc}") from exc

    if data is None:
        return []

    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        items = data.get("items", [])
        if items is None:
            return []
        if not isinstance(items, list):
            raise BacklogPlanError("The 'items' key in the backlog file must contain a list of entries.")
        entries = items
    else:
        raise BacklogPlanError(
            f"Backlog file {path} must contain either a list of entries or a mapping with an 'items' list."
        )

    normalised: List[Dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise BacklogPlanError(
                f"Backlog entry at index {index} must be a mapping, got {type(entry).__name__}."
            )
        normalised.append(entry)
    return normalised


def _normalize_multiline(value: str | None) -> str:
    if not value:
        return ""
    lines = [line.rstrip() for line in value.splitlines()]
    normalized = "\n".join(lines).strip()
    return normalized


def _generate_entry_id(items: Iterable[Dict[str, Any]]) -> str:
    max_id = 0
    for entry in items:
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id.startswith(ID_PREFIX):
            continue
        suffix = entry_id[len(ID_PREFIX) :]
        try:
            numeric = int(suffix)
        except ValueError:
            continue
        max_id = max(max_id, numeric)
    return f"{ID_PREFIX}{max_id + 1:0{ID_PADDING}d}"


def _item_sort_key(entry: Dict[str, Any]) -> Tuple[int, str]:
    entry_id = entry.get("id")
    if isinstance(entry_id, str) and entry_id.startswith(ID_PREFIX):
        suffix = entry_id[len(ID_PREFIX) :]
        try:
            return int(suffix), entry_id
        except ValueError:
            pass
    return (sys.maxsize, str(entry_id))


def _ensure_entry(
    items: List[Dict[str, Any]],
    project_item_id: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    for entry in items:
        if str(entry.get("project_item_id")) == project_item_id:
            if "id" not in entry or not isinstance(entry["id"], str):
                entry["id"] = _generate_entry_id(items)
            return entry

    content = context.get("content") or {}
    title = _normalize_multiline(content.get("title")) or f"Project item {project_item_id}"
    summary = _normalize_multiline(content.get("body"))
    if not summary:
        summary = (
            "Automatically generated from GitHub Projects item. Update this summary "
            "with additional acceptance criteria."
        )

    new_entry = {
        "id": _generate_entry_id(items),
        "title": title,
        "status": "proposed",
        "summary": summary,
        "project_item_id": project_item_id,
        "codex_plan_url": None,
        "codex_plan_tasks": [],
        "codex_run_ids": [],
        "last_updated_by": "codex",
        "metadata": {
            "project": context.get("project"),
            "field_values": context.get("field_values"),
            "content_url": content.get("url"),
            "content_type": content.get("type"),
            "content_number": content.get("number"),
            "content_title": content.get("title"),
        },
    }
    items.append(new_entry)
    return new_entry


def _normalise_tasks(raw_tasks: Any) -> List[Dict[str, Any]]:
    if not raw_tasks:
        return []

    if isinstance(raw_tasks, list):
        tasks: List[Dict[str, Any]] = []
        for item in raw_tasks:
            if isinstance(item, dict):
                tasks.append(dict(item))
            else:
                tasks.append({"value": item})
        return tasks

    if isinstance(raw_tasks, dict):
        return [dict(raw_tasks)]

    return [{"value": raw_tasks}]


def _detect_plan_fields(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    plan_section = plan_data.get("plan") or {}
    spec_section = plan_data.get("spec") or plan_data.get("specKit") or plan_data.get("speckit") or {}

    plan_url = (
        spec_section.get("plan_url")
        or spec_section.get("planUrl")
        or plan_data.get("plan_url")
        or plan_data.get("planUrl")
        or plan_data.get("url")
        or plan_section.get("url")
    )

    tasks = (
        spec_section.get("tasks")
        or spec_section.get("task_list")
        or spec_section.get("items")
        or plan_data.get("tasks")
        or plan_section.get("tasks")
        or plan_data.get("task_ids")
        or plan_data.get("taskIds")
    )

    if plan_url is None:
        raise BacklogPlanError("Codex planning command did not return a plan URL.")

    normalised_tasks = _normalise_tasks(tasks)
    result = {"plan_url": str(plan_url), "tasks": normalised_tasks}

    spec_feature = spec_section.get("feature") or spec_section.get("slug") or spec_section.get("id")
    if spec_feature:
        result["spec_feature"] = str(spec_feature)

    spec_tasks_path = spec_section.get("tasks_path") or spec_section.get("tasksPath")
    if spec_tasks_path:
        result["spec_tasks_path"] = str(spec_tasks_path)

    return result


def _run_planning_command(command: str, context: Dict[str, Any]) -> Dict[str, Any]:
    args = shlex.split(command)
    try:
        completed = subprocess.run(
            args,
            input=json.dumps(context).encode("utf-8"),
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise BacklogPlanError(f"Planning command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace")
        stdout = exc.stdout.decode("utf-8", errors="replace")
        message = (
            "Codex planning command failed with exit code "
            f"{exc.returncode}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )
        raise BacklogPlanError(message) from exc

    stdout = completed.stdout.decode("utf-8", errors="replace").strip()
    if not stdout:
        raise BacklogPlanError("Codex planning command did not produce any output.")

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise BacklogPlanError("Codex planning command did not return valid JSON output.") from exc


def _update_entry(entry: Dict[str, Any], context: Dict[str, Any], plan: Dict[str, Any]) -> None:
    project_item_ref = context.get("project_item_id") or context.get("project_item_node_id")
    if project_item_ref is None:
        raise BacklogPlanError("Context JSON did not include a project item identifier.")

    entry["project_item_id"] = str(project_item_ref)
    entry["status"] = entry.get("status") or "proposed"
    entry["codex_plan_url"] = plan["plan_url"]
    entry["codex_plan_tasks"] = plan["tasks"]

    metadata = entry.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        entry["metadata"] = metadata
    project = context.get("project")
    if project is not None or "project" not in metadata:
        metadata["project"] = project

    metadata["field_values"] = context.get("field_values")

    if plan.get("spec_feature"):
        metadata["spec_feature"] = plan["spec_feature"]
    if plan.get("spec_tasks_path"):
        metadata["spec_tasks_path"] = plan["spec_tasks_path"]

    content = context.get("content") or {}
    if isinstance(content, dict):
        metadata["content_url"] = content.get("url")
        metadata["content_type"] = content.get("type")
        metadata["content_number"] = content.get("number")
        metadata["content_title"] = content.get("title")

    generated_at = datetime.now(timezone.utc).strftime(ISO_FORMAT)
    entry["codex_plan_generated_at"] = generated_at

    plan_history = entry.setdefault("plan_history", [])
    if isinstance(plan_history, list):
        plan_history.append(
            {
                "plan_url": plan["plan_url"],
                "tasks": copy.deepcopy(plan["tasks"]),
                "generated_at": generated_at,
            }
        )
    else:
        entry["plan_history"] = [
            {
                "plan_url": plan["plan_url"],
                "tasks": copy.deepcopy(plan["tasks"]),
                "generated_at": generated_at,
            }
        ]

    entry["last_updated_by"] = "codex"


def _write_backlog(path: Path, items: List[Dict[str, Any]]) -> None:
    sorted_items = list(items)
    sorted_items.sort(key=_item_sort_key)
    payload = {"items": sorted_items}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)
    except OSError as exc:  # pragma: no cover - hard to simulate reliably
        raise BacklogPlanError(f"Failed to write backlog file {path}: {exc}") from exc


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", required=True, help="Path to the backlog context JSON file.")
    parser.add_argument(
        "--backlog-file",
        default="backlog/backlog.yaml",
        help="Path to the backlog YAML file to update.",
    )
    parser.add_argument(
        "--command",
        default=None,
        help=(
            "Planning command to execute. Defaults to the CODEX_PLANNING_COMMAND environment "
            "variable or 'codex cloud tasks plan --format json'."
        ),
    )
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Skip planning when the backlog entry already contains a plan URL.",
    )
    parser.add_argument(
        "--result",
        default=None,
        help="Optional path to write the planning result JSON.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    context_path = Path(args.context)
    backlog_path = Path(args.backlog_file)

    context = _load_json(context_path)
    raw_id = context.get("project_item_id") or context.get("project_item_node_id")
    if not raw_id:
        raise BacklogPlanError(
            "Context JSON must include a project_item_id or project_item_node_id."
        )
    project_item_id = str(raw_id)

    items = _load_backlog(backlog_path)
    entry = _ensure_entry(items, project_item_id, context)

    if args.skip_if_exists and entry.get("codex_plan_url"):
        metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
        result = PlanResult(
            project_item_id=project_item_id,
            skipped=True,
            entry_id=entry.get("id"),
            plan_url=entry.get("codex_plan_url"),
            tasks=entry.get("codex_plan_tasks"),
            spec_feature=metadata.get("spec_feature"),
            spec_tasks_path=metadata.get("spec_tasks_path"),
        )
    else:
        command = (
            args.command
            or os.environ.get("CODEX_PLANNING_COMMAND")
            or "codex cloud tasks plan --format json"
        )
        plan_output = _run_planning_command(command, context)
        plan = _detect_plan_fields(plan_output)
        _update_entry(entry, context, plan)
        _write_backlog(backlog_path, items)
        result = PlanResult(
            project_item_id=project_item_id,
            skipped=False,
            entry_id=entry.get("id"),
            plan_url=plan["plan_url"],
            tasks=plan["tasks"],
            spec_feature=plan.get("spec_feature"),
            spec_tasks_path=plan.get("spec_tasks_path"),
        )

    if args.result:
        result_path = Path(args.result)
        try:
            with result_path.open("w", encoding="utf-8") as handle:
                json.dump(result.to_dict(), handle)
        except OSError as exc:  # pragma: no cover - hard to simulate reliably
            raise BacklogPlanError(f"Failed to write result JSON to {result_path}: {exc}") from exc

    json.dump(result.to_dict(), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
