#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: setup_container.sh [--pull] [--image-tag <tag>] [--build-local]

Options:
  --pull             Generate services that pull prebuilt images from GHCR (default)
  --image-tag <tag>  Use the specified image tag when pulling from GHCR
  --build-local      Use local Docker build contexts instead of pulling images
  -h, --help         Show this help message
USAGE
}

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TERRAFORM_DIR="$ROOT_DIR/infrastructure/terraform"
DEFAULT_OUTPUT_FILE="$ROOT_DIR/docker-compose.generated.yml"
OUTPUT_FILE_RAW="${VTOC_COMPOSE_FILENAME:-$DEFAULT_OUTPUT_FILE}"
if [[ "$OUTPUT_FILE_RAW" = /* ]]; then
  OUTPUT_FILE="$OUTPUT_FILE_RAW"
else
  OUTPUT_FILE="$ROOT_DIR/$OUTPUT_FILE_RAW"
fi
CONFIG_JSON="${VTOC_CONFIG_JSON:-}"
if [[ -z "$CONFIG_JSON" ]]; then
  CONFIG_JSON="{}"
fi
APPLY="${VTOC_SETUP_APPLY:-false}"
IMAGE_TAG="${VTOC_IMAGE_TAG:-main}"
IMAGE_REPO="${VTOC_IMAGE_REPO:-ghcr.io/pr-cybr/vtoc}"
USE_BUILD_LOCAL="${VTOC_BUILD_LOCAL:-false}"
COMPOSE_PLATFORM="${VTOC_COMPOSE_PLATFORM:-}"
PULL_IMAGES="${VTOC_PULL_IMAGES:-true}"

if [[ "$USE_BUILD_LOCAL" == "true" ]]; then
  PULL_IMAGES="false"
fi

export CONFIG_JSON

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      USE_BUILD_LOCAL="false"
      PULL_IMAGES="true"
      shift
      ;;
    --image-tag)
      if [[ $# -lt 2 ]]; then
        echo "--image-tag requires a value" >&2
        exit 1
      fi
      IMAGE_TAG="$2"
      USE_BUILD_LOCAL="false"
      PULL_IMAGES="true"
      shift 2
      ;;
    --build-local)
      USE_BUILD_LOCAL="true"
      PULL_IMAGES="false"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

CONFIG_BUNDLE_OVERRIDE_JSON="$(python - <<'PY'
import json
import os
import sys

raw = os.environ.get("CONFIG_JSON", "{}")
raw = raw.strip()
try:
    data = json.loads(raw)
except json.JSONDecodeError as exc:
    sys.stderr.write(f"Invalid VTOC_CONFIG_JSON payload: {exc}\n")
    sys.exit(1)

bundle = data.get("configBundle")
if bundle is None:
    sys.exit(0)

sys.stdout.write(json.dumps(bundle))
PY
)"

FALLBACK_BUNDLE_PATH="$ROOT_DIR/scripts/defaults/config_bundle.local.json"
if [[ ! -f "$FALLBACK_BUNDLE_PATH" ]]; then
  echo "Fallback bundle missing at $FALLBACK_BUNDLE_PATH" >&2
  exit 1
fi

TERRAFORM_BUNDLE_JSON=""
BUNDLE_SOURCE="fallback"

if [[ -n "$CONFIG_BUNDLE_OVERRIDE_JSON" ]]; then
  BUNDLE_SOURCE="override"
else
  if command -v terraform >/dev/null 2>&1; then
    if terraform -chdir="$TERRAFORM_DIR" init -input=false >/dev/null; then
      if TERRAFORM_BUNDLE_JSON="$(terraform -chdir="$TERRAFORM_DIR" output -json config_bundle)"; then
        BUNDLE_SOURCE="terraform"
      else
        echo "terraform output failed; falling back to local defaults." >&2
      fi
    else
      echo "terraform init failed; falling back to local defaults." >&2
    fi
  else
    echo "terraform binary not found; using local defaults." >&2
  fi
fi

case "$BUNDLE_SOURCE" in
  override)
    echo "Using config bundle override from VTOC_CONFIG_JSON."
    ;;
  terraform)
    echo "Using config bundle from Terraform outputs."
    ;;
  fallback)
    echo "Using local fallback config bundle at $FALLBACK_BUNDLE_PATH."
    ;;
esac

export ROOT_DIR OUTPUT_FILE CONFIG_JSON IMAGE_TAG IMAGE_REPO USE_BUILD_LOCAL TERRAFORM_DIR
export CONFIG_BUNDLE_OVERRIDE_JSON TERRAFORM_BUNDLE_JSON FALLBACK_BUNDLE_PATH BUNDLE_SOURCE
export COMPOSE_PLATFORM

python - <<'PY'
import json
import os
from pathlib import Path


def _coerce_env(source):
    return {key: "" if value is None else str(value) for key, value in source.items()}


def _ensure_value(target, key, value):
    if value is None:
        target.setdefault(key, "")
    else:
        target[key] = str(value)


def _maybe_get(mapping, *keys):
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return mapping.get(keys[-1], "")

root_dir = Path(os.environ["ROOT_DIR"])
output_file = Path(os.environ["OUTPUT_FILE"])
config = json.loads(os.environ.get("CONFIG_JSON", "{}"))
image_repo = os.environ.get("IMAGE_REPO", "ghcr.io/pr-cybr/vtoc")
image_tag = os.environ.get("IMAGE_TAG", "latest")
use_build_local = os.environ.get("USE_BUILD_LOCAL", "false").lower() == "true"
bundle_source = os.environ.get("BUNDLE_SOURCE", "fallback")
override_json = os.environ.get("CONFIG_BUNDLE_OVERRIDE_JSON", "")
terraform_bundle_json = os.environ.get("TERRAFORM_BUNDLE_JSON", "")
fallback_bundle_path = Path(os.environ["FALLBACK_BUNDLE_PATH"])
compose_platform = os.environ.get("COMPOSE_PLATFORM", "").strip()

if bundle_source == "override" and override_json:
    bundle_raw = override_json
elif bundle_source == "terraform" and terraform_bundle_json:
    bundle_raw = terraform_bundle_json
else:
    bundle_raw = fallback_bundle_path.read_text()

bundle = json.loads(bundle_raw)
if "value" in bundle:
    bundle = bundle["value"]

services_config = config.get("services", {})
postgres_enabled = services_config.get("postgres", True)
traefik_enabled = services_config.get("traefik", False)
n8n_enabled = services_config.get("n8n", False)
wazuh_enabled = services_config.get("wazuh", False)

backend_env_internal = _coerce_env(bundle["backend"]["env"])
backend_env_public = _coerce_env(bundle["backend"]["env_public"])
backend_env = dict(backend_env_internal if postgres_enabled else backend_env_public)

frontend_env = _coerce_env(bundle.get("frontend", {}).get("env", {}))

chatkit_config = bundle.get("chatkit", {})
if chatkit_config:
    allowed_tools = chatkit_config.get("allowedTools")
    if isinstance(allowed_tools, (list, tuple, set)):
        allowed_tools = ",".join(str(item) for item in allowed_tools)

    _ensure_value(backend_env, "CHATKIT_API_KEY", chatkit_config.get("apiKey"))
    _ensure_value(backend_env, "CHATKIT_ORG_ID", chatkit_config.get("orgId"))
    _ensure_value(backend_env, "CHATKIT_WEBHOOK_SECRET", chatkit_config.get("webhookSecret"))
    _ensure_value(backend_env, "CHATKIT_ALLOWED_TOOLS", allowed_tools)

    _ensure_value(frontend_env, "VITE_CHATKIT_WIDGET_URL", chatkit_config.get("widgetUrl"))
    _ensure_value(frontend_env, "VITE_CHATKIT_API_KEY", chatkit_config.get("apiKey"))
    _ensure_value(frontend_env, "VITE_CHATKIT_TELEMETRY_CHANNEL", chatkit_config.get("telemetryChannel"))

agentkit_config = bundle.get("agentkit", {})
if agentkit_config:
    _ensure_value(backend_env, "AGENTKIT_API_BASE_URL", agentkit_config.get("apiBaseUrl"))
    _ensure_value(backend_env, "AGENTKIT_API_KEY", agentkit_config.get("apiKey"))
    _ensure_value(backend_env, "AGENTKIT_ORG_ID", agentkit_config.get("orgId"))
    _ensure_value(backend_env, "AGENTKIT_TIMEOUT_SECONDS", agentkit_config.get("timeoutSeconds"))

    _ensure_value(frontend_env, "VITE_AGENTKIT_ORG_ID", agentkit_config.get("orgId"))
    _ensure_value(frontend_env, "VITE_AGENTKIT_DEFAULT_STATION_CONTEXT", agentkit_config.get("defaultStationContext"))
    _ensure_value(frontend_env, "VITE_AGENTKIT_API_BASE_PATH", agentkit_config.get("apiBasePath"))

supabase_config = bundle.get("supabase", {})
if supabase_config:
    url = _maybe_get(supabase_config, "url", "api_url")
    project_ref = _maybe_get(supabase_config, "projectRef", "project_ref")
    anon_key = _maybe_get(supabase_config, "anonKey", "anon_key")
    service_role_key = _maybe_get(supabase_config, "serviceRoleKey", "service_role_key")
    jwt_secret = _maybe_get(supabase_config, "jwtSecret", "jwt_secret")

    _ensure_value(backend_env, "SUPABASE_URL", url)
    _ensure_value(backend_env, "SUPABASE_PROJECT_REF", project_ref)
    _ensure_value(backend_env, "SUPABASE_SERVICE_ROLE_KEY", service_role_key)
    _ensure_value(backend_env, "SUPABASE_JWT_SECRET", jwt_secret)
    _ensure_value(backend_env, "SUPABASE_ANON_KEY", anon_key)

    _ensure_value(frontend_env, "VITE_SUPABASE_URL", url)
    _ensure_value(frontend_env, "VITE_SUPABASE_ANON_KEY", anon_key)

compose = {
    "version": "3.8",
    "services": {
        "backend": {
            "ports": ["8080:8080"],
            "environment": backend_env,
            "depends_on": ["database"] if postgres_enabled else [],
        },
        "frontend": {
            "ports": ["8081:8081"],
            "environment": frontend_env,
            "depends_on": ["backend"],
        },
        "scraper": {
            "environment": bundle["scraper"]["env"],
            "depends_on": ["backend"],
        },
    },
    "networks": {"default": {"driver": "bridge"}},
}

if not use_build_local:
    compose["services"]["backend"].update(
        {
            "image": f"{image_repo}/backend:{image_tag}",
            "pull_policy": "always",
        }
    )
    compose["services"]["frontend"].update(
        {
            "image": f"{image_repo}/frontend:{image_tag}",
            "pull_policy": "always",
        }
    )
    compose["services"]["scraper"].update(
        {
            "image": f"{image_repo}/scraper:{image_tag}",
            "pull_policy": "always",
        }
    )
else:
    compose["services"]["backend"]["build"] = {"context": "./backend"}
    compose["services"]["frontend"]["build"] = {"context": "./frontend"}
    compose["services"]["scraper"]["build"] = {"context": "./agents/scraper"}

if postgres_enabled:
    postgres = bundle["postgres"]
    compose.setdefault("volumes", {})["postgres_data"] = {}
    compose["services"]["database"] = {
        "image": "postgres:15-alpine",
        "environment": {
            "POSTGRES_DB": postgres["database"],
            "POSTGRES_USER": postgres["user"],
            "POSTGRES_PASSWORD": postgres["password"],
        },
        "volumes": [
            "postgres_data:/var/lib/postgresql/data",
            "./database/init:/docker-entrypoint-initdb.d",
        ],
        "ports": ["5432:5432"],
    }
else:
    compose["services"]["backend"].pop("depends_on", None)

if traefik_enabled:
    compose["services"]["traefik"] = {
        "image": "traefik:v2.11",
        "command": [
            "--providers.docker=true",
            "--providers.docker.exposedbydefault=false",
            "--entrypoints.web.address=:80",
        ],
        "ports": ["80:80"],
        "volumes": ["/var/run/docker.sock:/var/run/docker.sock:ro"],
    }
    compose["services"]["backend"]["labels"] = [
        "traefik.enable=true",
        "traefik.http.routers.backend.rule=Host(`api.vtoc.local`)",
        "traefik.http.services.backend.loadbalancer.server.port=8080",
    ]
    compose["services"]["frontend"]["labels"] = [
        "traefik.enable=true",
        "traefik.http.routers.frontend.rule=Host(`vtoc.local`)",
        "traefik.http.services.frontend.loadbalancer.server.port=8081",
    ]

if n8n_enabled:
    compose["services"]["n8n"] = {
        "image": "n8nio/n8n:latest",
        "ports": ["5678:5678"],
    }

if wazuh_enabled:
    compose["services"]["wazuh-manager"] = {
        "image": "wazuh/wazuh-manager:4.7.5",
        "ports": ["55000:55000"],
    }

if compose_platform:
    for service in compose["services"].values():
        service["platform"] = compose_platform
        build = service.get("build")
        if isinstance(build, dict):
            build.setdefault("platform", compose_platform)


def dump_yaml(value, indent=0):
    spaces = "  " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}{key}:")
                lines.extend(dump_yaml(item, indent + 1))
            else:
                lines.append(f"{spaces}{key}: {item}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}-")
                lines.extend(dump_yaml(item, indent + 1))
            else:
                lines.append(f"{spaces}- {item}")
        return lines
    return [f"{spaces}{value}"]

lines = dump_yaml(compose)
output_file.parent.mkdir(parents=True, exist_ok=True)
output_file.write_text("\n".join(lines) + "\n")
PY

if [[ "$PULL_IMAGES" == "true" ]]; then
  for service in backend frontend scraper; do
    docker pull "${IMAGE_REPO}/${service}:${IMAGE_TAG}"
  done
fi

if [[ "$APPLY" == "true" ]]; then
  docker compose -f "$OUTPUT_FILE" up -d
else
  printf 'Generated %s. Run `docker compose -f %s up -d` to start containers.\n' "$OUTPUT_FILE" "$OUTPUT_FILE"
fi
