"""Command-line interface wrapping vTOC bootstrap workflows.

The CLI mirrors the developer Makefile so Windows or non-POSIX users can
invoke the same automation tasks without `make`. Each subcommand delegates
to the existing shell scripts or runs the equivalent commands directly.

The :mod:`spec` command group proxies GitHub's Spec Kit (`specify`) CLI so
developers can run planning workflows without installing additional tools.
Spec Kit relies on several environment variables that the wrapper documents
and forwards to subprocesses:

``SPECIFY_FEATURE``
    Feature flag sent to Spec Kit. Defaults to ``"bootstrap"`` when unset.

``CODEX_API_KEY`` / ``CODEX_BASE_URL``
    Credentials and endpoint used by Spec Kit when contacting Codex. These
    must be present in the environment before invoking the wrapper.

The wrapper automatically executes from the repository root and uses ``uvx``
to fetch Spec Kit unless a ``SPECIFY_BIN`` override is provided.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence

from scripts.bootstrap.local import DEFAULT_CONFIG_JSON
from scripts.automation.spec_tasks import SpecTaskError, sync_spec_tasks, validate_spec_tasks

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
SCRAPER_DIR = REPO_ROOT / "agents" / "scraper"
STATIONS_DIR = REPO_ROOT / "stations"
DEFAULT_STATIONS = ("TOC-S1", "TOC-S2", "TOC-S3", "TOC-S4")
PYTHON = sys.executable or "python"
SPEC_KIT_PACKAGE = "git+https://github.com/github/spec-kit.git"
SPECIFY_EXECUTABLE_ENV = "SPECIFY_BIN"
SPECIFY_DEFAULT_FEATURE = "bootstrap"


def _echo_command(command: Sequence[str]) -> None:
    quoted = " ".join(shlex.quote(str(arg)) for arg in command)
    print(f"$ {quoted}")


def run_command(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> None:
    """Run *command* and exit with the same status on failure."""

    command = [str(arg) for arg in command]
    _echo_command(command)
    merged_env = None
    if env is not None:
        merged_env = os.environ.copy()
        merged_env.update(env)
    try:
        subprocess.run(command, cwd=cwd, check=True, env=merged_env)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - passthrough
        raise SystemExit(exc.returncode) from exc


def load_config_payload(args: argparse.Namespace) -> str:
    if args.config_json:
        return args.config_json
    if args.config:
        if not args.config.exists():
            raise SystemExit(f"Configuration file not found: {args.config}")
        return args.config.read_text()
    env_payload = os.environ.get("VTOC_CONFIG_JSON")
    if env_payload:
        return env_payload
    return json.dumps(DEFAULT_CONFIG_JSON)


def run_setup(
    mode: str,
    *,
    config: Path | None,
    config_json: str | None,
    apply: bool,
    configure: bool,
) -> None:
    script = SCRIPTS_DIR / "setup.sh"
    if not script.exists():
        raise SystemExit("setup.sh script is missing; cannot continue")

    base_command: list[str]
    if sys.platform == "win32":
        base_command = ["bash", str(script)]
    else:
        base_command = [str(script)]

    processed_config_json: str | None = None
    if config_json:
        inline = config_json
        if inline.startswith("@"):
            file_path = Path(inline[1:])
            if not file_path.exists():
                raise SystemExit(f"Config JSON file not found: {file_path}")
            inline = file_path.read_text()
        inline = inline.strip()
        if inline:
            try:
                parsed = json.loads(inline)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON payload for --config-json: {exc}") from exc
            processed_config_json = json.dumps(parsed)
    
    args: list[str] = base_command + ["--mode", mode]
    if config:
        args += ["--config", str(config)]
    if processed_config_json:
        args += ["--config-json", processed_config_json]
    if apply:
        args.append("--apply")
    if configure:
        args.append("--configure")

    run_command(args)
    print_follow_up_instructions(mode)


FOLLOW_UP_STEPS: dict[str, list[str]] = {
    "local": [
        "Source the generated env files: `set -a; source .env.local .env.station; set +a`.",
        "Start the backend API: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8080`.",
        "Start the frontend dev server: `pnpm --dir frontend dev`.",
    ],
    "container": [
        "Review docker-compose.generated.yml then run `python -m scripts.bootstrap_cli compose up` to launch the stack.",
    ],
    "cloud": [
        "Inspect infrastructure/terraform and run `terraform apply` once secrets are configured.",
    ],
}


def print_follow_up_instructions(mode: str) -> None:
    steps = FOLLOW_UP_STEPS.get(mode)
    if not steps:
        return
    print("\n=== Next steps ===")
    for index, step in enumerate(steps, start=1):
        print(f"{index}. {step}")
    payload = {"mode": mode, "steps": steps}
    print(f"NEXT_STEPS::{json.dumps(payload)}")


def setup_command_factory(mode: str):
    if mode == "local":
        def command(args: argparse.Namespace) -> None:
            run_local_bootstrap(args)

        return command

    def command(args: argparse.Namespace) -> None:
        run_setup(
            mode,
            config=args.config,
            config_json=args.config_json,
            apply=args.apply,
            configure=args.configure,
        )

    return command


def run_local_bootstrap(args: argparse.Namespace) -> None:
    payload = load_config_payload(args)
    env = os.environ.copy()
    env["VTOC_CONFIG_JSON"] = payload
    command = [
        PYTHON,
        "-m",
        "scripts.bootstrap.local",
        "--terraform-dir",
        str(REPO_ROOT / "infrastructure" / "terraform"),
    ]
    run_command(command, env=env)


def _resolve_specify_command(subcommand: str, extra_args: Sequence[str]) -> list[str]:
    override = os.environ.get(SPECIFY_EXECUTABLE_ENV)
    if override:
        command = [override, subcommand]
    else:
        command = [
            "uvx",
            "--from",
            SPEC_KIT_PACKAGE,
            "specify",
            subcommand,
        ]
    passthrough = list(extra_args)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    return command + passthrough


def run_spec_command(subcommand: str, extra_args: Sequence[str]) -> None:
    command = _resolve_specify_command(subcommand, extra_args)
    feature = os.environ.get("SPECIFY_FEATURE") or SPECIFY_DEFAULT_FEATURE
    env = {"SPECIFY_FEATURE": feature}
    run_command(command, cwd=REPO_ROOT, env=env)


def add_setup_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to JSON configuration file passed to setup.sh",
    )
    parser.add_argument(
        "--config-json",
        help=(
            "Inline JSON configuration string (matches scripts/inputs.schema.json). "
            "Prefix with @path to read from a file."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply infrastructure changes when supported",
    )
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Run configuration management when supported",
    )


def compose_up(args: argparse.Namespace) -> None:
    command = [
        "docker",
        "compose",
        "-f",
        str(args.compose_file),
        "up",
    ]
    if args.detach:
        command.append("-d")
    run_command(command)


def compose_down(args: argparse.Namespace) -> None:
    command = [
        "docker",
        "compose",
        "-f",
        str(args.compose_file),
        "down",
    ]
    run_command(command)


def backend_test(_: argparse.Namespace) -> None:
    run_command([PYTHON, "-m", "pytest", "-q"], cwd=BACKEND_DIR)


def backend_lint(_: argparse.Namespace) -> None:
    run_command(["ruff", "check", "app"], cwd=BACKEND_DIR)


def frontend_test(_: argparse.Namespace) -> None:
    run_command(["pnpm", "test", "--", "--watch=false", "--passWithNoTests"], cwd=FRONTEND_DIR)


def scraper_run(_: argparse.Namespace) -> None:
    run_command([PYTHON, "main.py"], cwd=SCRAPER_DIR)


def spec_sync(args: argparse.Namespace) -> None:
    feature = args.feature or os.environ.get("SPECIFY_FEATURE", "")
    tasks_path = args.tasks_path
    if tasks_path is not None:
        tasks_path = Path(tasks_path)
    try:
        sync_spec_tasks(
            feature=feature,
            plan_result=Path(args.plan_result),
            tasks_path=tasks_path,
        )
    except SpecTaskError as exc:
        raise SystemExit(str(exc)) from exc


def spec_check(args: argparse.Namespace) -> None:
    base = Path(args.base) if args.base else REPO_ROOT / "specs"
    try:
        validate_spec_tasks(base)
    except SpecTaskError as exc:
        raise SystemExit(str(exc)) from exc


def station_migrate(args: argparse.Namespace) -> None:
    stations = args.station or DEFAULT_STATIONS
    for station in stations:
        script = STATIONS_DIR / station / "onboard.sh"
        if not script.exists():
            raise SystemExit(f"Station {station} is missing onboard.sh")
        if sys.platform == "win32":
            command = ["bash", str(script)]
        else:
            command = [str(script)]
        run_command(command)


def station_seed(args: argparse.Namespace) -> None:
    stations = args.station or DEFAULT_STATIONS
    for station in stations:
        seed_script = STATIONS_DIR / station / "seed.py"
        if not seed_script.exists():
            raise SystemExit(f"Station {station} is missing seed.py")
        run_command([PYTHON, str(seed_script)])


def add_station_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--station",
        action="append",
        metavar="NAME",
        help=(
            "Specific station(s) to operate on. May be provided multiple times. "
            "Defaults to TOC-S1 through TOC-S4."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="vTOC bootstrap CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # setup group
    setup_parser = subparsers.add_parser("setup", help="Run environment setup scripts")
    setup_subparsers = setup_parser.add_subparsers(dest="setup_command")

    setup_local = setup_subparsers.add_parser("local", help="Generate local env files")
    add_setup_options(setup_local)
    setup_local.set_defaults(func=setup_command_factory("local"))

    setup_container = setup_subparsers.add_parser(
        "container",
        help="Generate container configuration",
    )
    add_setup_options(setup_container)
    setup_container.set_defaults(func=setup_command_factory("container"))

    setup_cloud = setup_subparsers.add_parser(
        "cloud",
        help="Generate infrastructure scaffolding",
    )
    add_setup_options(setup_cloud)
    setup_cloud.set_defaults(func=setup_command_factory("cloud"))

    # compose group
    compose_parser = subparsers.add_parser("compose", help="Docker Compose helpers")
    compose_subparsers = compose_parser.add_subparsers(dest="compose_command")

    compose_up_parser = compose_subparsers.add_parser("up", help="Start the generated stack")
    compose_up_parser.add_argument(
        "--compose-file",
        default=REPO_ROOT / "docker-compose.generated.yml",
        type=Path,
        help="Compose file to use (defaults to docker-compose.generated.yml)",
    )
    compose_up_parser.add_argument(
        "--no-detach",
        dest="detach",
        action="store_false",
        help="Run containers in the foreground",
    )
    compose_up_parser.set_defaults(detach=True, func=compose_up)

    compose_down_parser = compose_subparsers.add_parser("down", help="Stop the generated stack")
    compose_down_parser.add_argument(
        "--compose-file",
        default=REPO_ROOT / "docker-compose.generated.yml",
        type=Path,
        help="Compose file to use (defaults to docker-compose.generated.yml)",
    )
    compose_down_parser.set_defaults(func=compose_down)

    # backend group
    backend_parser = subparsers.add_parser("backend", help="Backend developer utilities")
    backend_subparsers = backend_parser.add_subparsers(dest="backend_command")

    backend_test_parser = backend_subparsers.add_parser("test", help="Run backend pytest suite")
    backend_test_parser.set_defaults(func=backend_test)

    backend_lint_parser = backend_subparsers.add_parser("lint", help="Run backend linters")
    backend_lint_parser.set_defaults(func=backend_lint)

    # frontend group
    frontend_parser = subparsers.add_parser("frontend", help="Frontend developer utilities")
    frontend_subparsers = frontend_parser.add_subparsers(dest="frontend_command")

    frontend_test_parser = frontend_subparsers.add_parser("test", help="Run frontend tests")
    frontend_test_parser.set_defaults(func=frontend_test)

    # scraper group
    scraper_parser = subparsers.add_parser("scraper", help="Automation agent helpers")
    scraper_subparsers = scraper_parser.add_subparsers(dest="scraper_command")

    scraper_run_parser = scraper_subparsers.add_parser("run", help="Run the telemetry scraper")
    scraper_run_parser.set_defaults(func=scraper_run)

    # spec group
    spec_parser = subparsers.add_parser("spec", help="Spec Kit automation")
    spec_subparsers = spec_parser.add_subparsers(dest="spec_command")
    spec_subparsers.required = True

    spec_sync_parser = spec_subparsers.add_parser("sync", help="Update Spec Kit tasks from a Codex plan result")
    spec_sync_parser.add_argument("--plan-result", required=True, type=Path, help="Path to backlog/plan-result.json")
    spec_sync_parser.add_argument("--feature", help="Feature slug (defaults to SPECIFY_FEATURE or plan metadata)")
    spec_sync_parser.add_argument("--tasks-path", type=Path, help="Override the generated tasks.md path")
    spec_sync_parser.set_defaults(func=spec_sync)

    spec_check_parser = spec_subparsers.add_parser("check", help="Validate generated Spec Kit task files")
    spec_check_parser.add_argument("--base", type=Path, default=REPO_ROOT / "specs", help="Base directory of Spec Kit features")
    spec_check_parser.set_defaults(func=spec_check)

    # station group
    station_parser = subparsers.add_parser("station", help="Station bootstrap helpers")
    station_subparsers = station_parser.add_subparsers(dest="station_command")

    station_migrate_parser = station_subparsers.add_parser(
        "migrate",
        help="Run station onboarding scripts",
    )
    add_station_arguments(station_migrate_parser)
    station_migrate_parser.set_defaults(func=station_migrate)

    station_seed_parser = station_subparsers.add_parser(
        "seed",
        help="Seed baseline telemetry for stations",
    )
    add_station_arguments(station_seed_parser)
    station_seed_parser.set_defaults(func=station_seed)

    # spec group
    spec_parser = subparsers.add_parser(
        "spec",
        help="Spec Kit ideation helpers",
        description=(
            "Run Spec Kit planning commands against the repository.\n\n"
            "Environment:\n"
            f"  SPECIFY_FEATURE   Feature flag forwarded to Spec Kit (default: {SPECIFY_DEFAULT_FEATURE})\n"
            "  CODEX_API_KEY     Codex API token required for authenticated requests\n"
            "  CODEX_BASE_URL    Optional Codex endpoint override\n"
            "Set SPECIFY_BIN to reuse a vendored Spec Kit executable instead of uvx.\n\n"
            "Append `--` before extra arguments to forward them directly to Spec Kit."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    spec_subparsers = spec_parser.add_subparsers(dest="spec_command")

    def register_spec_subcommand(name: str, help_text: str) -> None:
        sub = spec_subparsers.add_parser(
            name,
            help=help_text,
            description=help_text,
        )
        sub.add_argument(
            "args",
            nargs=argparse.REMAINDER,
            help="Arguments forwarded directly to Spec Kit",
        )
        sub.set_defaults(func=lambda args, n=name: run_spec_command(n, args.args))

    register_spec_subcommand(
        "constitution",
        "Generate or review the project's Spec Kit constitution",
    )
    register_spec_subcommand(
        "specify",
        "Run arbitrary Spec Kit commands via the `specify` entry point",
    )
    register_spec_subcommand(
        "plan",
        "Draft implementation plans using Spec Kit",
    )
    register_spec_subcommand(
        "tasks",
        "Break down work into trackable tasks using Spec Kit",
    )
    register_spec_subcommand(
        "implement",
        "Follow Spec Kit's implementation guidance",
    )

    return parser


def dispatch(args: argparse.Namespace) -> None:
    if not hasattr(args, "func"):
        raise SystemExit(build_parser().format_help())
    args.func(args)


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        parser.exit(1)
    dispatch(args)


if __name__ == "__main__":
    main()
