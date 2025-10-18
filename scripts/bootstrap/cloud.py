"""Cloud scaffolding generator used by setup_cloud.sh.

The module provides a reusable entrypoint for producing Terraform and
Ansible assets from the resolved configuration bundle. It mirrors the
container bootstrap flow: prefer an inline ``configBundle`` override,
attempt to hydrate from Terraform state, and fall back to the
development defaults when no state is available. Structured metadata is
emitted alongside the generated files so AI assistants (or humans) can
report next steps to operators.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TERRAFORM_SOURCE_DIR = REPO_ROOT / "infrastructure" / "terraform"
DEFAULT_FALLBACK_BUNDLE_PATH = REPO_ROOT / "scripts" / "defaults" / "config_bundle.local.json"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "infra"
MANIFEST_FILENAME = "cloud-manifest.json"


class CloudGenerationError(RuntimeError):
    """Raised when the generator cannot continue."""


@dataclass
class GenerationResult:
    """Container for generation side effects."""

    manifest: Dict[str, Any]
    manifest_path: Path
    terraform_dir: Path
    ansible_dir: Path
    bundle_source: str
    backend_ip: str | None
    messages: List[str]


def _load_config_payload(config_json: str | None, config_path: Path | None) -> str:
    if config_json:
        return config_json
    if config_path:
        try:
            return config_path.read_text()
        except OSError as exc:  # pragma: no cover - surfaced to CLI
            raise CloudGenerationError(f"Failed to read config file {config_path}: {exc}") from exc
    if "VTOC_CONFIG_JSON" in os.environ:
        return os.environ["VTOC_CONFIG_JSON"]
    return "{}"


def _parse_config(payload: str) -> Dict[str, Any]:
    payload = payload.strip()
    if not payload:
        payload = "{}"
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CloudGenerationError(f"Invalid configuration JSON: {exc}") from exc


def _ensure_terraform_init(terraform_dir: Path) -> bool:
    terraform_bin = shutil.which("terraform")
    if terraform_bin is None:
        return False
    try:
        subprocess.run(
            [terraform_bin, "-chdir", str(terraform_dir), "init", "-input=false"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def _terraform_output_json(terraform_dir: Path, output_name: str) -> Tuple[str | None, List[str]]:
    terraform_bin = shutil.which("terraform")
    if terraform_bin is None:
        return None, ["terraform binary not found; falling back to defaults"]

    init_success = _ensure_terraform_init(terraform_dir)
    messages: List[str] = []
    if not init_success:
        messages.append("terraform init failed; falling back to defaults if outputs are missing")

    try:
        completed = subprocess.run(
            [terraform_bin, "-chdir", str(terraform_dir), "output", "-json", output_name],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        messages.append(
            f"terraform output '{output_name}' failed with exit code {exc.returncode};"
            " defaults will be used if no override is provided"
        )
        return None, messages

    return completed.stdout, messages


def resolve_config_bundle(
    config: Dict[str, Any],
    terraform_source_dir: Path,
    fallback_bundle_path: Path,
) -> Tuple[Dict[str, Any], str, List[str]]:
    bundle_override = config.get("configBundle")
    if bundle_override is not None:
        return bundle_override, "override", []

    bundle_raw, messages = _terraform_output_json(terraform_source_dir, "config_bundle")
    if bundle_raw:
        try:
            bundle = json.loads(bundle_raw)
        except json.JSONDecodeError:
            messages.append("terraform output produced invalid JSON; using fallback bundle")
        else:
            if isinstance(bundle, dict) and "value" in bundle:
                bundle = bundle["value"]
            return bundle, "terraform", messages

    if not fallback_bundle_path.exists():
        raise CloudGenerationError(f"Fallback bundle missing at {fallback_bundle_path}")

    bundle = json.loads(fallback_bundle_path.read_text())
    messages.append(f"Using fallback config bundle at {fallback_bundle_path}")
    return bundle, "fallback", messages


def _quote_single(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _jinja_default(var_name: str, default: str) -> str:
    return "{{ " + var_name + " | default(" + json.dumps(default) + ") }}"


def _write_terraform_files(terraform_dir: Path, provider: str, region: str, project: str) -> None:
    terraform_dir.mkdir(parents=True, exist_ok=True)

    main_tf = (
        "terraform {\n"
        "  required_version = \"\u003e= 1.5.0\"\n"
        "  required_providers {\n"
        f"    {provider} = {{ source = \"hashicorp/{provider}\" }}\n"
        "  }\n"
        "}\n\n"
        f"provider \"{provider}\" {{\n"
        f"  region = \"{region}\"\n"
        "}\n\n"
        f"resource \"{provider}_instance\" \"vtoc\" {{\n"
        "  ami           = var.ami\n"
        "  instance_type = var.instance_type\n"
        "  tags = {\n"
        f"    Name = \"{project}-backend\"\n"
        "  }\n"
        "}}\n"
    )
    (terraform_dir / "main.tf").write_text(main_tf)

    variables_tf = (
        "variable \"ami\" {\n"
        "  description = \"Base AMI ID\"\n"
        "  type        = string\n"
        "}\n\n"
        "variable \"instance_type\" {\n"
        "  description = \"Compute instance type\"\n"
        "  type        = string\n"
        "  default     = \"t3.micro\"\n"
        "}\n"
    )
    (terraform_dir / "variables.tf").write_text(variables_tf)

    outputs_tf = (
        "output \"backend_ip\" {\n"
        f"  value = {provider}_instance.vtoc.public_ip\n"
        "}\n"
    )
    (terraform_dir / "outputs.tf").write_text(outputs_tf)


def _station_lines(bundle: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    backend_public_env = bundle.get("backend", {}).get("env_public", {})
    station_env_lines: List[str] = []
    station_vars_lines: List[str] = []

    for key in sorted(backend_public_env):
        if key == "DATABASE_URL":
            continue
        value = str(backend_public_env[key])
        station_env_lines.append(
            "          {key}: \"{{{{ station_urls.{key} | default({value}) }}}}\"".format(
                key=key,
                value=_quote_single(value),
            )
        )
        station_vars_lines.append(f"    {key}: {_quote_single(value)}")

    return station_env_lines, station_vars_lines


def _write_ansible_files(
    ansible_dir: Path,
    bundle: Dict[str, Any],
    backend_image: str,
    backend_ip: str | None,
    terraform_dir: Path,
) -> str:
    ansible_dir.mkdir(parents=True, exist_ok=True)
    group_vars_dir = ansible_dir / "group_vars"
    group_vars_dir.mkdir(parents=True, exist_ok=True)

    inventory_lines = ["[vtoc]"]
    if backend_ip:
        inventory_lines.append(f"backend ansible_host={backend_ip}")
        host_source = "terraform-output"
    else:
        inventory_lines.append("backend ansible_host={{ backend_ip }}")
        host_source = "lookup-command"
    (ansible_dir / "inventory.ini").write_text("\n".join(inventory_lines) + "\n")

    backend_public_env = bundle.get("backend", {}).get("env_public", {})
    database_url_default = str(backend_public_env.get("DATABASE_URL", ""))
    station_env_lines, station_vars_lines = _station_lines(bundle)

    playbook_lines: List[str] = [
        "---",
        "- name: Configure vTOC backend host",
        "  hosts: vtoc",
        "  become: true",
        "  vars:",
        f"    docker_image: {_jinja_default('docker_image', backend_image)}",
        f"    database_url: {_jinja_default('database_url', database_url_default)}",
    ]
    playbook_lines.extend(station_vars_lines)
    playbook_lines.extend(
        [
            "  tasks:",
            "    - name: Ensure Docker is installed",
            "      ansible.builtin.package:",
            "        name: docker.io",
            "        state: present",
            "",
            "    - name: Run backend container",
            "      community.docker.docker_container:",
            "        name: vtoc-backend",
            "        image: \"{{ docker_image }}\"",
            "        restart_policy: unless-stopped",
            "        env:",
            "          DATABASE_URL: \"{{ database_url }}\"",
        ]
    )
    playbook_lines.extend(station_env_lines)
    playbook_lines.extend(
        [
            "        published_ports:",
            "          - \"8080:8080\"",
        ]
    )
    (ansible_dir / "playbook.yml").write_text("\n".join(playbook_lines) + "\n")

    rel_path = os.path.relpath(terraform_dir, ansible_dir)
    rel_posix = Path(rel_path).as_posix()
    if backend_ip:
        backend_ip_value = _quote_single(backend_ip)
    else:
        lookup_expr = "{{ lookup('pipe', 'terraform -chdir=" + rel_posix + " output -raw backend_ip') }}"
        backend_ip_value = f'"{lookup_expr}"'

    group_vars_lines = ["---", f"backend_ip: {backend_ip_value}"]
    (group_vars_dir / "all.yml").write_text("\n".join(group_vars_lines) + "\n")

    return host_source


def _collect_missing_keys(section: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    missing: List[str] = []
    provided: List[str] = []
    for key, value in section.items():
        if isinstance(value, str):
            if value:
                provided.append(key)
            else:
                missing.append(key)
    return sorted(missing), sorted(provided)


def _backend_ip_from_outputs(terraform_dir: Path) -> Tuple[str | None, List[str]]:
    terraform_bin = shutil.which("terraform")
    if terraform_bin is None:
        return None, ["terraform binary not found while resolving backend_ip"]

    try:
        completed = subprocess.run(
            [terraform_bin, "-chdir", str(terraform_dir), "output", "-raw", "backend_ip"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None, ["terraform output backend_ip failed"]

    return completed.stdout.strip(), []


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def generate_cloud_assets(
    config: Dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    terraform_source_dir: Path | None = None,
    output_root: Path | None = None,
    fallback_bundle_path: Path | None = None,
    apply: bool = False,
    configure: bool = False,
) -> GenerationResult:
    terraform_source_dir = terraform_source_dir or DEFAULT_TERRAFORM_SOURCE_DIR
    output_root = output_root or DEFAULT_OUTPUT_ROOT
    fallback_bundle_path = fallback_bundle_path or DEFAULT_FALLBACK_BUNDLE_PATH

    bundle, bundle_source, bundle_messages = resolve_config_bundle(
        config,
        terraform_source_dir,
        fallback_bundle_path,
    )

    cloud_config = config.get("cloud", {})
    provider = cloud_config.get("provider", "aws")
    region = cloud_config.get("region", "us-east-1")
    project = config.get("projectName", "vtoc")

    terraform_dir = output_root / "terraform"
    ansible_dir = output_root / "ansible"

    _write_terraform_files(terraform_dir, provider, region, project)

    backend_image_default = bundle.get("fly", {}).get("runtime", {}).get(
        "backend_image",
        "ghcr.io/pr-cybr/vtoc/backend:latest",
    )

    backend_ip, backend_ip_messages = _backend_ip_from_outputs(terraform_dir)

    host_source = _write_ansible_files(
        ansible_dir,
        bundle,
        backend_image_default or "ghcr.io/pr-cybr/vtoc/backend:latest",
        backend_ip,
        terraform_dir,
    )

    messages = bundle_messages + backend_ip_messages

    if apply:
        terraform_bin = shutil.which("terraform")
        if terraform_bin is None:
            raise CloudGenerationError("terraform binary is required when --apply is set")
        subprocess.run(
            [terraform_bin, "-chdir", str(terraform_dir), "init", "-input=false"],
            check=True,
        )
        subprocess.run(
            [terraform_bin, "-chdir", str(terraform_dir), "apply", "-auto-approve"],
            check=True,
        )
        backend_ip, backend_ip_messages = _backend_ip_from_outputs(terraform_dir)
        messages.extend(backend_ip_messages)
        host_source = _write_ansible_files(
            ansible_dir,
            bundle,
            backend_image_default or "ghcr.io/pr-cybr/vtoc/backend:latest",
            backend_ip,
            terraform_dir,
        )

    if configure:
        ansible_bin = shutil.which("ansible-playbook")
        if ansible_bin is None:
            raise CloudGenerationError("ansible-playbook is required when --configure is set")
        subprocess.run(
            [
                ansible_bin,
                "-i",
                str(ansible_dir / "inventory.ini"),
                str(ansible_dir / "playbook.yml"),
            ],
            check=True,
        )

    backend_env_public = bundle.get("backend", {}).get("env_public", {})
    fly_runtime = bundle.get("fly", {}).get("runtime", {})
    supabase_config = bundle.get("supabase", {})
    fly_secrets_env = bundle.get("fly", {}).get("secrets_env", {})

    backend_missing, backend_provided = _collect_missing_keys(backend_env_public)
    fly_missing, fly_provided = _collect_missing_keys(fly_secrets_env)
    supabase_missing, supabase_provided = _collect_missing_keys(supabase_config)

    terraform_rel = _relative_path(terraform_dir, repo_root)
    ansible_rel = _relative_path(ansible_dir, repo_root)

    commands = {
        "terraform_init": f"terraform -chdir {terraform_rel} init",
        "terraform_plan": f"terraform -chdir {terraform_rel} plan",
        "terraform_apply": f"terraform -chdir {terraform_rel} apply -auto-approve",
        "ansible_configure": f"ansible-playbook -i {ansible_rel}/inventory.ini {ansible_rel}/playbook.yml",
    }

    manifest_path = output_root / MANIFEST_FILENAME
    manifest_rel = _relative_path(manifest_path, repo_root)

    next_steps: List[str] = [
        f"Review {manifest_rel} for required secrets and environment overrides.",
        f"Run `{commands['terraform_init']}` to prepare providers.",
        f"Apply infrastructure with `{commands['terraform_apply']}`.",
        "Run the Ansible playbook once the backend IP is available to configure Docker.",
    ]
    if not backend_ip:
        next_steps.insert(
            2,
            f"Capture the backend host IP with `terraform -chdir {terraform_rel} output -raw backend_ip` after apply.",
        )

    manifest = {
        "bundleSource": bundle_source,
        "provider": provider,
        "region": region,
        "project": project,
        "outputRoot": _relative_path(output_root, repo_root),
        "images": {
            "backend": backend_image_default,
            "frontend": fly_runtime.get("frontend_image", ""),
            "scraper": fly_runtime.get("scraper_image", ""),
        },
        "inventory": {
            "host": backend_ip,
            "source": host_source,
            "path": _relative_path(ansible_dir / "inventory.ini", output_root),
        },
        "secrets": {
            "backend_env_public": {
                "missing": backend_missing,
                "provided": backend_provided,
            },
            "fly_secrets_env": {
                "missing": fly_missing,
                "provided": fly_provided,
            },
            "supabase": {
                "missing": supabase_missing,
                "provided": supabase_provided,
            },
        },
        "commands": commands,
        "nextSteps": next_steps,
        "warnings": messages,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    return GenerationResult(
        manifest=manifest,
        manifest_path=manifest_path,
        terraform_dir=terraform_dir,
        ansible_dir=ansible_dir,
        bundle_source=bundle_source,
        backend_ip=backend_ip,
        messages=messages,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Terraform and Ansible assets for cloud deployments")
    parser.add_argument("--config-json", help="Inline JSON configuration payload")
    parser.add_argument("--config", type=Path, help="Path to configuration JSON file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory where infra assets should be written (defaults to repo infra/)",
    )
    parser.add_argument(
        "--terraform-source",
        type=Path,
        default=DEFAULT_TERRAFORM_SOURCE_DIR,
        help="Existing Terraform directory containing state/outputs for config bundle resolution",
    )
    parser.add_argument(
        "--fallback-bundle",
        type=Path,
        default=DEFAULT_FALLBACK_BUNDLE_PATH,
        help="Fallback config bundle JSON used when Terraform outputs are unavailable",
    )
    parser.add_argument("--apply", action="store_true", help="Run terraform apply after generating assets")
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Run ansible-playbook after generating assets (requires reachable backend host)",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        payload = _load_config_payload(args.config_json, args.config)
        config = _parse_config(payload)
        result = generate_cloud_assets(
            config,
            repo_root=REPO_ROOT,
            terraform_source_dir=args.terraform_source,
            output_root=args.output_dir,
            fallback_bundle_path=args.fallback_bundle,
            apply=args.apply,
            configure=args.configure,
        )
    except CloudGenerationError as exc:
        parser.error(str(exc))
        return 2
    except subprocess.CalledProcessError as exc:  # pragma: no cover - surfaced to shell
        return exc.returncode

    print(f"Cloud scaffolding generated in {result.manifest_path.parent}")
    print(f"Structured manifest written to {result.manifest_path}")
    print(json.dumps(result.manifest, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
