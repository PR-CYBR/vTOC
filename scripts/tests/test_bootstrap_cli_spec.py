from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts import bootstrap_cli


def test_resolve_specify_command_uses_uvx_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(bootstrap_cli.SPECIFY_EXECUTABLE_ENV, raising=False)
    command = bootstrap_cli._resolve_specify_command("plan", ["--", "--dry-run", "--verbose"])
    assert command[:5] == [
        "uvx",
        "--from",
        bootstrap_cli.SPEC_KIT_PACKAGE,
        "specify",
        "plan",
    ]
    assert command[5:] == ["--dry-run", "--verbose"]


def test_run_spec_command_sets_default_feature_and_cwd(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_run_command(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
        captured["command"] = command
        captured["cwd"] = cwd
        captured["env"] = env

    monkeypatch.setattr(bootstrap_cli, "run_command", fake_run_command)
    monkeypatch.delenv("SPECIFY_FEATURE", raising=False)
    monkeypatch.delenv(bootstrap_cli.SPECIFY_EXECUTABLE_ENV, raising=False)

    bootstrap_cli.run_spec_command("plan", [])

    assert captured["command"][:5] == [
        "uvx",
        "--from",
        bootstrap_cli.SPEC_KIT_PACKAGE,
        "specify",
        "plan",
    ]
    assert captured["cwd"] == bootstrap_cli.REPO_ROOT
    assert captured["env"] == {"SPECIFY_FEATURE": bootstrap_cli.SPECIFY_DEFAULT_FEATURE}


def test_run_spec_command_respects_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_run_command(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
        captured["command"] = command
        captured["cwd"] = cwd
        captured["env"] = env

    monkeypatch.setattr(bootstrap_cli, "run_command", fake_run_command)
    monkeypatch.setenv("SPECIFY_FEATURE", "vtoc")
    monkeypatch.setenv(bootstrap_cli.SPECIFY_EXECUTABLE_ENV, "/tmp/specify")

    bootstrap_cli.run_spec_command("tasks", ["--dry-run"])

    assert captured["command"] == ["/tmp/specify", "tasks", "--dry-run"]
    assert captured["cwd"] == bootstrap_cli.REPO_ROOT
    assert captured["env"] == {"SPECIFY_FEATURE": "vtoc"}


def test_spec_parser_passes_through_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = bootstrap_cli.build_parser()
    args = parser.parse_args(["spec", "implement", "--", "--fast", "--owner", "@vtoc"])

    called: dict[str, Any] = {}

    def fake_run_spec_command(subcommand: str, extra_args: list[str]) -> None:
        called["subcommand"] = subcommand
        called["extra_args"] = extra_args

    monkeypatch.setattr(bootstrap_cli, "run_spec_command", fake_run_spec_command)

    args.func(args)

    assert called == {
        "subcommand": "implement",
        "extra_args": ["--", "--fast", "--owner", "@vtoc"],
    }
