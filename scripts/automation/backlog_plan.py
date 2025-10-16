#!/usr/bin/env python3
"""Generate a Codex Cloud plan for a backlog entry and persist it to backlog.yaml."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency resolution handled by workflow
    raise SystemExit("PyYAML must be installed to use backlog_plan.py") from exc


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_backlog(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"items": {}}

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise SystemExit(f"Backlog file {path} must contain a mapping at the top level.")

    items = data.get("items")
    if items is None:
        items = {}
    elif not isinstance(items, dict):
        raise SystemExit("The 'items' key in the backlog file must map to a dictionary.")

    data["items"] = items
    return data


def _ensure_entry(backlog: Dict[str, Any], project_item_id: str) -> Dict[str, Any]:
    items = backlog.setdefault("items", {})
    if not isinstance(items, dict):
        raise SystemExit("The 'items' key in the backlog file must map to a dictionary.")

    entry = items.get(project_item_id)
    if entry is None:
        entry = {"project_item_id": project_item_id}
        items[project_item_id] = entry
    elif not isinstance(entry, dict):
        raise SystemExit("Backlog entries must be dictionaries.")

    return entry


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
    # Attempt to normalise different response shapes from the Codex planning command.
    plan_url = (
        plan_data.get("plan_url")
        or plan_data.get("planUrl")
        or plan_data.get("url")
        or plan_data.get("plan", {}).get("url")
    )

    tasks = (
        plan_data.get("tasks")
        or plan_data.get("plan", {}).get("tasks")
        or plan_data.get("task_ids")
        or plan_data.get("taskIds")
    )

    if plan_url is None:
        raise SystemExit("Codex planning command did not return a plan URL.")

    normalised_tasks = _normalise_tasks(tasks)

    return {"plan_url": plan_url, "tasks": normalised_tasks}


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
        raise SystemExit(f"Planning command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace")
        stdout = exc.stdout.decode("utf-8", errors="replace")
        message = (
            "Codex planning command failed with exit code"
            f" {exc.returncode}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )
        raise SystemExit(message) from exc

    stdout = completed.stdout.decode("utf-8", errors="replace").strip()
    if not stdout:
        raise SystemExit("Codex planning command did not produce any output.")

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            "Codex planning command did not return valid JSON output."
        ) from exc


def _update_entry(entry: Dict[str, Any], context: Dict[str, Any], plan: Dict[str, Any]) -> None:
    content = context.get("content")
    project = context.get("project")

    if content:
        entry["content"] = content
    if project:
        entry["project"] = project

    entry["status"] = context.get("status")
    entry["project_item_node_id"] = context.get("project_item_node_id")
    entry["updated_at"] = datetime.now(timezone.utc).isoformat()

    entry.setdefault("history", []).append(
        {
            "plan_url": plan["plan_url"],
            "tasks": plan["tasks"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    entry["plan"] = plan


def _write_backlog(path: Path, backlog: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(backlog, handle, sort_keys=False)


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
        help="Planning command to execute. Defaults to the CODEX_PLANNING_COMMAND environment variable,"
        " or 'codex cloud tasks plan --format json' if not provided.",
    )
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Skip planning when the backlog entry already contains a plan.",
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

    project_item_id = str(context.get("project_item_id") or context.get("project_item_node_id"))
    if not project_item_id:
        raise SystemExit("Context JSON must include a project_item_id or project_item_node_id.")

    backlog = _load_backlog(backlog_path)
    entry = _ensure_entry(backlog, project_item_id)

    if args.skip_if_exists and entry.get("plan"):
        result = {
            "project_item_id": project_item_id,
            "skipped": True,
            "reason": "plan already recorded",
        }
    else:
        command = (
            args.command
            or os.environ.get("CODEX_PLANNING_COMMAND")
            or "codex cloud tasks plan --format json"
        )

        plan_output = _run_planning_command(command, context)
        plan = _detect_plan_fields(plan_output)

        _update_entry(entry, context, plan)
        _write_backlog(backlog_path, backlog)

        result = {
            "project_item_id": project_item_id,
            "plan_url": plan["plan_url"],
            "tasks": plan["tasks"],
            "skipped": False,
        }

    if args.result:
        with Path(args.result).open("w", encoding="utf-8") as handle:
            json.dump(result, handle)

    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
