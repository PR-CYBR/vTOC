#!/usr/bin/env python3
"""Utilities for synchronising Spec Kit task files with Codex planning outputs."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


class SpecTaskError(Exception):
    """Raised when synchronising or validating Spec Kit tasks fails."""


@dataclass
class PlanPayload:
    project_item_id: str | None
    skipped: bool
    tasks: List[dict] | None
    spec_feature: str | None
    spec_tasks_path: str | None

    @classmethod
    def from_json(cls, payload: dict) -> "PlanPayload":
        project_item_id = payload.get("project_item_id")
        skipped = bool(payload.get("skipped"))
        raw_tasks = payload.get("tasks") or payload.get("codex_plan_tasks")
        tasks: List[dict] | None = None
        if isinstance(raw_tasks, list):
            tasks = []
            for item in raw_tasks:
                if isinstance(item, dict):
                    tasks.append(dict(item))
                else:
                    tasks.append({"value": item})
        elif isinstance(raw_tasks, dict):
            tasks = [dict(raw_tasks)]
        elif raw_tasks is not None:
            tasks = [{"value": raw_tasks}]
        spec_feature = payload.get("spec_feature")
        spec_tasks_path = payload.get("spec_tasks_path")
        return cls(
            project_item_id=str(project_item_id) if project_item_id is not None else None,
            skipped=skipped,
            tasks=tasks,
            spec_feature=str(spec_feature) if spec_feature else None,
            spec_tasks_path=str(spec_tasks_path) if spec_tasks_path else None,
        )

    def update_payload(self, payload: dict) -> None:
        if self.spec_feature:
            payload["spec_feature"] = self.spec_feature
        if self.spec_tasks_path:
            payload["spec_tasks_path"] = self.spec_tasks_path


def _load_plan_result(path: Path) -> tuple[dict, PlanPayload]:
    if not path.exists():
        raise SpecTaskError(f"Plan result file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - diagnostics depend on file
        raise SpecTaskError(f"Plan result file {path} does not contain valid JSON: {exc}") from exc
    plan = PlanPayload.from_json(payload)
    return payload, plan


def _normalise_feature(raw_feature: str | None) -> str:
    if not raw_feature:
        return ""
    slug = raw_feature.strip().lower().replace(" ", "-")
    cleaned = []
    for char in slug:
        if char.isalnum() or char in {"-", "_", "/"}:
            cleaned.append(char)
    while cleaned and cleaned[0] in {"-", "_", "/"}:
        cleaned.pop(0)
    while cleaned and cleaned[-1] in {"-", "_", "/"}:
        cleaned.pop()
    return "".join(cleaned)


def _render_tasks(feature: str, tasks: Iterable[dict]) -> str:
    lines: List[str] = ["# Tasks", ""]
    if feature:
        lines.append(f"_Feature: `{feature}`_")
        lines.append("")
    for task in tasks:
        title = str(task.get("title") or task.get("summary") or task.get("value") or "Task")
        status = task.get("status") or task.get("state")
        prefix = "- [ ]"
        if isinstance(status, str) and status.lower() in {"done", "complete", "completed", "true"}:
            prefix = "- [x]"
        lines.append(f"{prefix} {title}".rstrip())
        details = task.get("details") or task.get("description")
        if isinstance(details, str) and details.strip():
            for detail_line in details.strip().splitlines():
                lines.append(f"  - {detail_line.rstrip()}")
    if len(lines) == 2:  # no tasks appended
        lines.append("_No tasks synchronised from the latest plan run._")
    lines.append("")
    return "\n".join(lines)


def sync_spec_tasks(*, feature: str, plan_result: Path, tasks_path: Path | None = None) -> Path | None:
    payload, plan = _load_plan_result(plan_result)
    normalised_feature = _normalise_feature(feature or plan.spec_feature)
    if plan.skipped:
        if normalised_feature:
            plan.spec_feature = normalised_feature
            plan.update_payload(payload)
            plan_result.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if plan.spec_tasks_path:
            return Path(plan.spec_tasks_path)
        return None

    tasks = plan.tasks
    if not tasks:
        raise SpecTaskError("Plan result did not include any tasks to sync to Spec Kit.")
    if not normalised_feature:
        raise SpecTaskError(
            "A feature identifier is required to update Spec Kit tasks. Provide --feature or set SPECIFY_FEATURE."
        )

    target_path = tasks_path or Path("specs") / normalised_feature / "tasks.md"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = _render_tasks(normalised_feature, tasks)
    target_path.write_text(rendered, encoding="utf-8")

    plan.spec_feature = normalised_feature
    plan.spec_tasks_path = str(target_path)
    plan.update_payload(payload)
    plan_result.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target_path


def validate_spec_tasks(base_dir: Path | None = None) -> None:
    base = base_dir or Path("specs")
    if not base.exists():
        return  # nothing to validate yet
    violations: List[str] = []
    for tasks_file in sorted(base.glob("**/tasks.md")):
        try:
            content = tasks_file.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - filesystem specific
            violations.append(f"{tasks_file}: unable to read file ({exc})")
            continue
        if "# Tasks" not in content:
            violations.append(f"{tasks_file}: missing '# Tasks' heading")
        if "- [" not in content:
            violations.append(f"{tasks_file}: expected at least one checklist item")
    if violations:
        joined = "\n".join(violations)
        raise SpecTaskError(f"Spec Kit task validation failed:\n{joined}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Synchronise tasks.md for a feature using a Codex plan result")
    sync_parser.add_argument(
        "--feature",
        required=False,
        help="Spec feature slug (defaults to SPECIFY_FEATURE or plan result metadata)",
    )
    sync_parser.add_argument(
        "--plan-result", required=True, type=Path, help="Path to the plan result JSON emitted by backlog_plan.py"
    )
    sync_parser.add_argument("--tasks-path", type=Path, help="Override the output tasks.md path")

    check_parser = subparsers.add_parser("check", help="Validate all generated Spec Kit task files")
    check_parser.add_argument("--base", type=Path, default=Path("specs"), help="Base directory containing Spec Kit features")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "sync":
            env_feature = os.environ.get("SPECIFY_FEATURE", "")
            sync_spec_tasks(
                feature=args.feature or env_feature,
                plan_result=args.plan_result,
                tasks_path=args.tasks_path,
            )
        elif args.command == "check":
            validate_spec_tasks(args.base)
        else:  # pragma: no cover - defensive
            parser.error(f"Unsupported command: {args.command}")
    except SpecTaskError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
