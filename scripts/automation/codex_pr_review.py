#!/usr/bin/env python3
"""Run Codex CLI against a pull request diff to assess risk."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MAX_DIFF_CHARS = 16000
DEFAULT_MODEL = "gpt-4.1"


@dataclass
class GitRange:
    base: str
    head: str


class CodexReviewError(Exception):
    """Raised when the Codex review fails."""


def run_git_diff(git_range: GitRange) -> str:
    try:
        completed = subprocess.run(
            ["git", "diff", "--unified=0", f"{git_range.base}..{git_range.head}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise CodexReviewError(
            f"Unable to gather diff between {git_range.base} and {git_range.head}: {exc.stderr.strip()}"
        ) from exc
    return completed.stdout


def trim_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n...\n[diff truncated, {len(text) - max_chars} additional characters omitted]"


def determine_cli_path() -> str:
    env = os.environ
    return env.get("CODEX_BIN") or env.get("code") or "codex"


def invoke_codex(cli_path: str, model: str, prompt: str) -> str:
    env = os.environ.copy()
    try:
        completed = subprocess.run(
            [cli_path, "chat", "--model", model, "--input", prompt],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except FileNotFoundError as exc:  # pragma: no cover - environment specific
        raise CodexReviewError(f"Codex CLI not found at {cli_path}: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        raise CodexReviewError(
            f"Codex CLI exited with status {exc.returncode}: {exc.stderr.strip()}"
        ) from exc
    return completed.stdout.strip()


PROMPT_TEMPLATE = """You are assisting with an automated pull request review.

Assess the provided git diff and summarize the changes. Determine the overall risk
level for merging: use one of LOW, MEDIUM, or HIGH. High risk should be reserved for
changes that likely break builds, deployments, or critical functionality without
additional review.

Return a JSON object with the following structure:
{
  "risk_level": "LOW | MEDIUM | HIGH",
  "summary": "one to two sentence summary of the change",
  "recommendations": ["actionable follow-up items, if any"],
  "notes": "additional context for reviewers"
}

Do not include any extra text outside of the JSON. Reference specific files when
useful. Diff:
"""


def build_prompt(diff: str) -> str:
    return f"{PROMPT_TEMPLATE}\n{diff.strip()}"


def parse_response(response: str) -> dict[str, Any]:
    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise CodexReviewError(
            "Codex CLI returned a non-JSON response."
        ) from exc

    if not isinstance(data, dict):
        raise CodexReviewError("Codex response must be a JSON object.")

    risk = str(data.get("risk_level", "")).strip().upper()
    if risk not in {"LOW", "MEDIUM", "HIGH"}:
        raise CodexReviewError(
            "Codex response missing risk_level or it is not one of LOW, MEDIUM, HIGH."
        )

    summary = str(data.get("summary", "")).strip()
    if not summary:
        raise CodexReviewError("Codex response missing summary text.")

    recommendations = data.get("recommendations", [])
    if not isinstance(recommendations, list):
        raise CodexReviewError("Recommendations must be a list of strings.")
    cleaned_recommendations = [str(item).strip() for item in recommendations if str(item).strip()]

    notes = str(data.get("notes", "")).strip()

    return {
        "risk_level": risk,
        "summary": summary,
        "recommendations": cleaned_recommendations,
        "notes": notes,
    }


def write_output(path: Path, data: dict[str, Any]) -> None:
    try:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise CodexReviewError(f"Unable to write output file {path}: {exc}") from exc


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Codex risk review on a pull request diff.")
    parser.add_argument("--base", required=True, help="Base commit SHA for the diff.")
    parser.add_argument("--head", required=True, help="Head commit SHA for the diff.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Codex model name.")
    parser.add_argument(
        "--max-diff-chars",
        type=int,
        default=DEFAULT_MAX_DIFF_CHARS,
        help="Maximum number of diff characters to include in the prompt.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("review.json"),
        help="Path to write the review JSON output.",
    )
    args = parser.parse_args(argv)

    git_range = GitRange(base=args.base, head=args.head)
    diff = run_git_diff(git_range)
    trimmed_diff = trim_text(diff, args.max_diff_chars)
    prompt = build_prompt(trimmed_diff)

    cli_path = determine_cli_path()
    response = invoke_codex(cli_path, args.model, prompt)
    parsed = parse_response(response)
    parsed.update(
        {
            "base": git_range.base,
            "head": git_range.head,
            "model": args.model,
        }
    )
    write_output(args.output, parsed)
    print(parsed["summary"])
    print(f"Risk level: {parsed['risk_level']}")
    if parsed["recommendations"]:
        print("Recommendations:")
        for item in parsed["recommendations"]:
            print(f"- {item}")
    if parsed["notes"]:
        print(f"Notes: {parsed['notes']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except CodexReviewError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        raise SystemExit(1)
