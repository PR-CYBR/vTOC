"""Local bootstrap utilities for generating development artifacts."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, MutableMapping, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CONFIG_JSON = {
    "projectName": "vtoc",
    "services": {
        "traefik": False,
        "postgres": True,
        "n8n": False,
        "wazuh": False,
    },
}

JsonDict = Dict[str, Any]
Emitter = Callable[[str, Mapping[str, Any]], None]


class BootstrapError(RuntimeError):
    """Raised when the bootstrap workflow cannot continue."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def emit(event: str, payload: Mapping[str, Any]) -> None:
    """Emit a structured log payload for downstream tooling."""

    frame: Dict[str, Any] = {"event": event, **payload}
    print(json.dumps(frame, sort_keys=True))


def parse_config_payload(raw: str | None, *, emitter: Emitter) -> JsonDict:
    raw = (raw or "").strip()
    if not raw:
        emitter("vtoc.local.config", {"status": "default"})
        return json.loads(json.dumps(DEFAULT_CONFIG_JSON))

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        emitter(
            "vtoc.local.config",
            {
                "status": "error",
                "error": f"Invalid configuration JSON: {exc}",
            },
        )
        raise BootstrapError("Unable to parse configuration JSON") from exc

    emitter("vtoc.local.config", {"status": "loaded"})
    return data


def _normalize_bundle(bundle: JsonDict) -> JsonDict:
    if "value" in bundle and isinstance(bundle["value"], dict):
        return bundle["value"]
    return bundle


@dataclass
class BundleSelection:
    bundle: JsonDict
    source: str


def fetch_terraform_bundle(
    terraform_dir: Path,
    *,
    emitter: Emitter,
) -> Tuple[JsonDict | None, str | None]:
    terraform_bin = shutil.which("terraform")
    if terraform_bin is None:
        emitter(
            "vtoc.local.terraform",
            {"status": "unavailable", "reason": "not_found"},
        )
        return None, "not_found"

    init_cmd = [terraform_bin, "-chdir", str(terraform_dir), "init", "-input=false"]
    emitter(
        "vtoc.local.terraform",
        {"status": "init", "command": init_cmd},
    )
    init_result = subprocess.run(
        init_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if init_result.returncode != 0:
        emitter(
            "vtoc.local.terraform",
            {
                "status": "error",
                "reason": "init_failed",
                "returncode": init_result.returncode,
                "stderr": init_result.stderr.strip(),
            },
        )
        return None, "init_failed"

    output_cmd = [
        terraform_bin,
        "-chdir",
        str(terraform_dir),
        "output",
        "-json",
        "config_bundle",
    ]
    emitter(
        "vtoc.local.terraform",
        {"status": "output", "command": output_cmd},
    )
    output_result = subprocess.run(
        output_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if output_result.returncode != 0:
        emitter(
            "vtoc.local.terraform",
            {
                "status": "error",
                "reason": "output_failed",
                "returncode": output_result.returncode,
                "stderr": output_result.stderr.strip(),
            },
        )
        return None, "output_failed"

    try:
        bundle_raw = json.loads(output_result.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        emitter(
            "vtoc.local.terraform",
            {
                "status": "error",
                "reason": "decode_failed",
                "stderr": output_result.stdout.strip(),
            },
        )
        return None, "decode_failed"

    bundle = _normalize_bundle(bundle_raw)
    emitter("vtoc.local.terraform", {"status": "success"})
    return bundle, None


def read_fallback_bundle(path: Path, *, emitter: Emitter) -> JsonDict:
    if not path.exists():
        emitter(
            "vtoc.local.fallback",
            {"status": "error", "reason": "missing", "path": str(path)},
        )
        raise BootstrapError(f"Fallback bundle missing at {path}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        emitter(
            "vtoc.local.fallback",
            {
                "status": "error",
                "reason": "decode_failed",
                "path": str(path),
            },
        )
        raise BootstrapError(f"Fallback bundle at {path} is not valid JSON") from exc
    emitter("vtoc.local.fallback", {"status": "loaded", "path": str(path)})
    return data


def resolve_config_bundle(
    config: JsonDict,
    terraform_dir: Path,
    fallback_path: Path,
    *,
    emitter: Emitter,
) -> BundleSelection:
    override = config.get("configBundle")
    if override is not None:
        emitter("vtoc.local.bundle", {"status": "selected", "source": "override"})
        if isinstance(override, str):
            try:
                override = json.loads(override)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise BootstrapError("configBundle override is not valid JSON") from exc
        if not isinstance(override, Mapping):
            raise BootstrapError("configBundle override must be a mapping")
        return BundleSelection(bundle=_normalize_bundle(override), source="override")

    bundle, failure_reason = fetch_terraform_bundle(terraform_dir, emitter=emitter)
    if bundle is not None:
        emitter("vtoc.local.bundle", {"status": "selected", "source": "terraform"})
        return BundleSelection(bundle=bundle, source="terraform")

    emitter(
        "vtoc.local.bundle",
        {"status": "fallback", "reason": failure_reason},
    )
    fallback_bundle = read_fallback_bundle(fallback_path, emitter=emitter)
    if not isinstance(fallback_bundle, Mapping):  # pragma: no cover - defensive
        raise BootstrapError("Fallback bundle payload must be a mapping")
    return BundleSelection(bundle=_normalize_bundle(fallback_bundle), source="fallback")


def render_env_lines(env: Mapping[str, Any]) -> str:
    pairs = []
    for key in sorted(env):
        value = env[key]
        pairs.append(f"{key}={value}")
    return "\n".join(pairs) + "\n"


def ensure_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise BootstrapError(f"Required executable '{name}' not found on PATH")


def run_command(
    command: Iterable[str],
    *,
    cwd: Path,
    emitter: Emitter,
    event: str,
) -> None:
    command_list = [str(arg) for arg in command]
    emitter(event, {"status": "running", "command": command_list, "cwd": str(cwd)})
    try:
        subprocess.run(command_list, cwd=cwd, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - passthrough
        emitter(
            event,
            {
                "status": "error",
                "returncode": exc.returncode,
            },
        )
        raise BootstrapError(f"Command failed: {' '.join(command_list)}") from exc
    emitter(event, {"status": "success"})


def _determine_config_source(args: argparse.Namespace) -> str | None:
    if args.config_json:
        return args.config_json
    if args.config:
        return Path(args.config).read_text()
    return os.environ.get("VTOC_CONFIG_JSON")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap local vTOC resources")
    parser.add_argument("--config-json", help="Inline JSON configuration payload")
    parser.add_argument("--config", help="Path to JSON configuration file")
    parser.add_argument(
        "--terraform-dir",
        type=Path,
        default=REPO_ROOT / "infrastructure" / "terraform",
        help="Directory containing Terraform configuration",
    )
    parser.add_argument(
        "--fallback-bundle",
        type=Path,
        default=REPO_ROOT / "scripts" / "defaults" / "config_bundle.local.json",
        help="Path to fallback configuration bundle",
    )
    parser.add_argument(
        "--frontend-dir",
        type=Path,
        default=REPO_ROOT / "frontend",
        help="Directory where the frontend project resides",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip pnpm install/build steps (primarily for testing)",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    emitter: Emitter = lambda event, payload: emit(event, payload)

    config_payload = _determine_config_source(args)
    config = parse_config_payload(config_payload, emitter=emitter)

    try:
        ensure_executable("pnpm")
    except BootstrapError as exc:
        emitter("vtoc.local.complete", {"status": "error", "error": str(exc)})
        return exc.exit_code

    selection: BundleSelection | None = None

    try:
        selection = resolve_config_bundle(
            config,
            args.terraform_dir,
            args.fallback_bundle,
            emitter=emitter,
        )

        frontend_env = selection.bundle.get("frontend", {}).get("env")
        if not isinstance(frontend_env, MutableMapping):
            raise BootstrapError("Frontend environment mapping missing from config bundle")

        frontend_dir = args.frontend_dir
        env_file = frontend_dir / ".env.local"
        env_file.parent.mkdir(parents=True, exist_ok=True)
        env_contents = render_env_lines(frontend_env)
        env_file.write_text(env_contents)
        emitter(
            "vtoc.local.env_file",
            {"status": "written", "path": str(env_file)},
        )

        if not args.skip_build:
            run_command(
                ["pnpm", "install", "--frozen-lockfile"],
                cwd=frontend_dir,
                emitter=emitter,
                event="vtoc.local.pnpm.install",
            )
            run_command(
                ["pnpm", "build"],
                cwd=frontend_dir,
                emitter=emitter,
                event="vtoc.local.pnpm.build",
            )

    except BootstrapError as exc:
        source = selection.source if selection is not None else "unknown"
        emitter(
            "vtoc.local.complete",
            {
                "status": "error",
                "error": str(exc),
                "bundleSource": source,
            },
        )
        return exc.exit_code

    emitter(
        "vtoc.local.complete",
        {"status": "success", "bundleSource": selection.source},
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main())
