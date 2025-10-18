"""Generate local environment files from the resolved configuration bundle.

The module is invoked from ``scripts/setup_local.sh`` and is responsible for
collecting ChatKit/AgentKit/Supabase secrets, prompting for missing metadata
when running interactively, and persisting the merged configuration to
``.env.local``, ``.env.station``, and ``frontend/.env.local``.

When non-interactive, the script trusts the forwarded ``VTOC_CONFIG_JSON``
payload which follows ``scripts/inputs.schema.json``. The schema now accepts
``chatkit``, ``agentkit``, ``supabase``, and ``station`` sections so the
bootstrap process can run unattended (for example through an AI assistant).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
FALLBACK_BUNDLE_PATH = ROOT_DIR / "scripts" / "defaults" / "config_bundle.local.json"
TERRAFORM_DIR = ROOT_DIR / "infrastructure" / "terraform"
PROMPT_PREFIX = "PROMPT"


class ConfigurationError(RuntimeError):
    """Raised when the forwarded configuration payload is malformed."""


def _load_config() -> Dict[str, Any]:
    raw = os.environ.get("VTOC_CONFIG_JSON", "{}")
    raw = raw.strip() or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise ConfigurationError(f"Invalid VTOC_CONFIG_JSON payload: {exc}") from exc


def _load_json_file(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise ConfigurationError(f"Missing configuration bundle at {path}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise ConfigurationError(f"Bundle at {path} is not valid JSON: {exc}") from exc


def _invoke_terraform_output() -> Dict[str, Any] | None:
    """Attempt to read the ``config_bundle`` Terraform output if available."""

    if shutil.which("terraform") is None:
        return None

    try:
        subprocess.run(
            ["terraform", "-chdir", str(TERRAFORM_DIR), "init", "-input=false"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        return None

    try:
        result = subprocess.run(
            ["terraform", "-chdir", str(TERRAFORM_DIR), "output", "-json", "config_bundle"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    if isinstance(data, dict) and "value" in data:
        return data["value"]
    return data


def _resolve_bundle(config: Dict[str, Any]) -> Dict[str, Any]:
    override = config.get("configBundle")
    if isinstance(override, dict):
        return override

    terraform_bundle = _invoke_terraform_output()
    if terraform_bundle:
        return terraform_bundle

    return _load_json_file(FALLBACK_BUNDLE_PATH)


def _ensure_section(config: Dict[str, Any], key: str) -> Dict[str, Any]:
    section = config.get(key)
    if section is None:
        section = {}
        config[key] = section
    return section


def _prompt_for_value(
    path: str,
    message: str,
    *,
    default: str = "",
    secret: bool = False,
) -> str:
    """Prompt the operator for a value when running interactively."""

    print(f"{PROMPT_PREFIX}[{path}]: {message}")
    prompt = message
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    if secret:
        response = getpass(prompt)
    else:
        response = input(prompt)
    return response.strip() or default


def _ensure_value(
    section: Dict[str, Any],
    key: str,
    message: str,
    *,
    default: str = "",
    secret: bool = False,
    path: str | None = None,
    interactive: bool,
) -> str:
    value = section.get(key)
    if value not in (None, ""):
        return str(value)

    default = str(default)
    if interactive:
        value = _prompt_for_value(path or key, message, default=default, secret=secret)
    else:
        value = default
    section[key] = value
    return value


def _stringify_env(env: Dict[str, Any]) -> Dict[str, str]:
    return {key: "" if value is None else str(value) for key, value in env.items()}


def _format_env_lines(env: Dict[str, str]) -> Iterable[str]:
    for key in sorted(env):
        value = env[key].replace("\\", "\\\\").replace("\n", "\\n")
        yield f"{key}={value}"


def _write_env_file(path: Path, env: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(_format_env_lines(env)) + "\n")
    rel = path.relative_to(ROOT_DIR)
    print(f"Wrote {rel} ({len(env)} entries)")


def _merge_chatkit(
    backend_env: Dict[str, str],
    frontend_env: Dict[str, str],
    chatkit: Dict[str, Any],
    *,
    interactive: bool,
) -> None:
    api_key = _ensure_value(
        chatkit,
        "apiKey",
        "ChatKit API key used by backend and agents",
        default=backend_env.get("CHATKIT_API_KEY", ""),
        secret=True,
        path="chatkit.apiKey",
        interactive=interactive,
    )
    org_id = _ensure_value(
        chatkit,
        "orgId",
        "ChatKit organization ID",
        default=backend_env.get("CHATKIT_ORG_ID", ""),
        path="chatkit.orgId",
        interactive=interactive,
    )
    webhook_secret = _ensure_value(
        chatkit,
        "webhookSecret",
        "Webhook signing secret for ChatKit callbacks",
        default=backend_env.get("CHATKIT_WEBHOOK_SECRET", ""),
        secret=True,
        path="chatkit.webhookSecret",
        interactive=interactive,
    )
    allowed_tools = _ensure_value(
        chatkit,
        "allowedTools",
        "Comma-separated list of tool identifiers allowed in ChatKit",
        default=backend_env.get("CHATKIT_ALLOWED_TOOLS", ""),
        path="chatkit.allowedTools",
        interactive=interactive,
    )
    widget_url = _ensure_value(
        chatkit,
        "widgetUrl",
        "ChatKit widget script URL for the frontend",
        default=frontend_env.get("VITE_CHATKIT_WIDGET_URL", ""),
        path="chatkit.widgetUrl",
        interactive=interactive,
    )
    telemetry_channel = _ensure_value(
        chatkit,
        "telemetryChannel",
        "Default telemetry channel name",
        default=frontend_env.get("VITE_CHATKIT_TELEMETRY_CHANNEL", ""),
        path="chatkit.telemetryChannel",
        interactive=interactive,
    )

    backend_env.update(
        {
            "CHATKIT_API_KEY": api_key,
            "CHATKIT_ORG_ID": org_id,
            "CHATKIT_WEBHOOK_SECRET": webhook_secret,
            "CHATKIT_ALLOWED_TOOLS": allowed_tools,
        }
    )
    frontend_env.update(
        {
            "VITE_CHATKIT_WIDGET_URL": widget_url,
            "VITE_CHATKIT_API_KEY": api_key,
            "VITE_CHATKIT_TELEMETRY_CHANNEL": telemetry_channel,
        }
    )


def _merge_agentkit(
    backend_env: Dict[str, str],
    frontend_env: Dict[str, str],
    agentkit: Dict[str, Any],
    *,
    interactive: bool,
) -> None:
    api_base_url = _ensure_value(
        agentkit,
        "apiBaseUrl",
        "AgentKit API base URL",
        default=backend_env.get("AGENTKIT_API_BASE_URL", ""),
        path="agentkit.apiBaseUrl",
        interactive=interactive,
    )
    api_key = _ensure_value(
        agentkit,
        "apiKey",
        "AgentKit API key",
        default=backend_env.get("AGENTKIT_API_KEY", ""),
        secret=True,
        path="agentkit.apiKey",
        interactive=interactive,
    )
    org_id = _ensure_value(
        agentkit,
        "orgId",
        "AgentKit organization ID",
        default=backend_env.get("AGENTKIT_ORG_ID", ""),
        path="agentkit.orgId",
        interactive=interactive,
    )
    timeout_seconds = _ensure_value(
        agentkit,
        "timeoutSeconds",
        "AgentKit request timeout (seconds)",
        default=backend_env.get("AGENTKIT_TIMEOUT_SECONDS", "30"),
        path="agentkit.timeoutSeconds",
        interactive=interactive,
    )
    default_station_context = _ensure_value(
        agentkit,
        "defaultStationContext",
        "Default station context for AgentKit widgets",
        default=frontend_env.get("VITE_AGENTKIT_DEFAULT_STATION_CONTEXT", ""),
        path="agentkit.defaultStationContext",
        interactive=interactive,
    )
    api_base_path = _ensure_value(
        agentkit,
        "apiBasePath",
        "Frontend API base path for AgentKit actions",
        default=frontend_env.get("VITE_AGENTKIT_API_BASE_PATH", "/api/v1/agent-actions"),
        path="agentkit.apiBasePath",
        interactive=interactive,
    )

    backend_env.update(
        {
            "AGENTKIT_API_BASE_URL": api_base_url,
            "AGENTKIT_API_KEY": api_key,
            "AGENTKIT_ORG_ID": org_id,
            "AGENTKIT_TIMEOUT_SECONDS": str(timeout_seconds),
        }
    )
    frontend_env.update(
        {
            "VITE_AGENTKIT_ORG_ID": org_id,
            "VITE_AGENTKIT_DEFAULT_STATION_CONTEXT": default_station_context,
            "VITE_AGENTKIT_API_BASE_PATH": api_base_path,
        }
    )


@dataclass
class SupabaseCredentials:
    url: str
    project_ref: str
    anon_key: str
    service_role_key: str
    jwt_secret: str


def _merge_supabase(
    backend_env: Dict[str, str],
    frontend_env: Dict[str, str],
    supabase: Dict[str, Any],
    *,
    interactive: bool,
) -> SupabaseCredentials:
    url = _ensure_value(
        supabase,
        "url",
        "Supabase project URL",
        default=backend_env.get("SUPABASE_URL", ""),
        path="supabase.url",
        interactive=interactive,
    )
    project_ref = _ensure_value(
        supabase,
        "projectRef",
        "Supabase project reference",
        default=backend_env.get("SUPABASE_PROJECT_REF", ""),
        path="supabase.projectRef",
        interactive=interactive,
    )
    anon_key = _ensure_value(
        supabase,
        "anonKey",
        "Supabase anon key (frontend safe)",
        default=frontend_env.get("VITE_SUPABASE_ANON_KEY", ""),
        secret=True,
        path="supabase.anonKey",
        interactive=interactive,
    )
    service_role_key = _ensure_value(
        supabase,
        "serviceRoleKey",
        "Supabase service-role key",
        default=backend_env.get("SUPABASE_SERVICE_ROLE_KEY", ""),
        secret=True,
        path="supabase.serviceRoleKey",
        interactive=interactive,
    )
    jwt_secret = _ensure_value(
        supabase,
        "jwtSecret",
        "Supabase JWT secret (optional)",
        default=backend_env.get("SUPABASE_JWT_SECRET", ""),
        secret=True,
        path="supabase.jwtSecret",
        interactive=interactive,
    )

    backend_env.update(
        {
            "SUPABASE_URL": url,
            "SUPABASE_PROJECT_REF": project_ref,
            "SUPABASE_SERVICE_ROLE_KEY": service_role_key,
            "SUPABASE_JWT_SECRET": jwt_secret,
            "SUPABASE_ANON_KEY": anon_key,
        }
    )
    frontend_env.update(
        {
            "VITE_SUPABASE_URL": url,
            "VITE_SUPABASE_ANON_KEY": anon_key,
        }
    )

    return SupabaseCredentials(
        url=url,
        project_ref=project_ref,
        anon_key=anon_key,
        service_role_key=service_role_key,
        jwt_secret=jwt_secret,
    )


def _build_station_env(
    station_config: Dict[str, Any],
    *,
    chatkit: Dict[str, Any],
    supabase_creds: SupabaseCredentials,
    interactive: bool,
    frontend_env: Dict[str, str],
) -> Dict[str, str]:
    default_role = station_config.get("role") or "ops"
    role = _ensure_value(
        station_config,
        "role",
        "Station role (ops/intel/logistics)",
        default=default_role,
        path="station.role",
        interactive=interactive,
    )
    default_callsign = station_config.get("callsign") or frontend_env.get("VITE_DEFAULT_DIV", "TOC-S1")
    callsign = _ensure_value(
        station_config,
        "callsign",
        "Station callsign",
        default=default_callsign,
        path="station.callsign",
        interactive=interactive,
    )
    telemetry_channel = station_config.get("telemetryChannel") or chatkit.get("telemetryChannel", "")
    if telemetry_channel:
        station_config["telemetryChannel"] = telemetry_channel
    mission_channel = station_config.get("missionChannel", "")

    station_env: Dict[str, str] = {
        "POSTGRES_STATION_ROLE": str(role),
        "STATION_CALLSIGN": str(callsign),
        "VITE_STATION_ROLE": str(role),
        "VITE_STATION_CALLSIGN": str(callsign),
        "SUPABASE_URL": supabase_creds.url,
        "SUPABASE_ANON_KEY": supabase_creds.anon_key,
    }

    if telemetry_channel:
        station_env["CHATKIT_TELEMETRY_CHANNEL"] = str(telemetry_channel)
    if mission_channel:
        station_env["CHATKIT_MISSION_CHANNEL"] = str(mission_channel)

    channel_cache = station_config.get("channelCache")
    if channel_cache:
        station_env["CHATKIT_CHANNEL_CACHE"] = json.dumps(channel_cache)

    return station_env


def main() -> None:
    interactive = sys.stdin.isatty()
    config = _load_config()
    bundle = _resolve_bundle(config)

    backend_env = _stringify_env(bundle.get("backend", {}).get("env", {}))
    frontend_env = _stringify_env(bundle.get("frontend", {}).get("env", {}))

    chatkit_config = _ensure_section(config, "chatkit")
    agentkit_config = _ensure_section(config, "agentkit")
    supabase_config = _ensure_section(config, "supabase")
    station_config = _ensure_section(config, "station")

    _merge_chatkit(backend_env, frontend_env, chatkit_config, interactive=interactive)
    _merge_agentkit(backend_env, frontend_env, agentkit_config, interactive=interactive)
    supabase_creds = _merge_supabase(
        backend_env,
        frontend_env,
        supabase_config,
        interactive=interactive,
    )

    station_env = _build_station_env(
        station_config,
        chatkit=chatkit_config,
        supabase_creds=supabase_creds,
        interactive=interactive,
        frontend_env=frontend_env,
    )

    _write_env_file(ROOT_DIR / ".env.local", backend_env)
    _write_env_file(ROOT_DIR / ".env.station", station_env)
    _write_env_file(FRONTEND_DIR / ".env.local", frontend_env)


if __name__ == "__main__":  # pragma: no cover - script entry point
    try:
        main()
    except ConfigurationError as exc:
        raise SystemExit(str(exc)) from exc
