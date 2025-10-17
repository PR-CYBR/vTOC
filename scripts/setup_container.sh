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
TERRAFORM_DIR="$ROOT_DIR/infrastructure"
OUTPUT_FILE="$ROOT_DIR/docker-compose.generated.yml"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"
APPLY="${VTOC_SETUP_APPLY:-false}"
IMAGE_TAG="${VTOC_IMAGE_TAG:-main}"
IMAGE_REPO="${VTOC_IMAGE_REPO:-ghcr.io/pr-cybr/vtoc}"
USE_BUILD_LOCAL="${VTOC_BUILD_LOCAL:-false}"
PULL_IMAGES="true"

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

terraform -chdir="$TERRAFORM_DIR" init -input=false >/dev/null

export ROOT_DIR OUTPUT_FILE CONFIG_JSON IMAGE_TAG IMAGE_REPO USE_BUILD_LOCAL TERRAFORM_DIR

python - <<'PY'
import json
import os
import subprocess
from pathlib import Path

root_dir = Path(os.environ["ROOT_DIR"])
output_file = Path(os.environ["OUTPUT_FILE"])
config = json.loads(os.environ.get("CONFIG_JSON", "{}"))
image_repo = os.environ.get("IMAGE_REPO", "ghcr.io/pr-cybr/vtoc")
image_tag = os.environ.get("IMAGE_TAG", "latest")
use_build_local = os.environ.get("USE_BUILD_LOCAL", "false").lower() == "true"
terraform_dir = Path(os.environ["TERRAFORM_DIR"])

try:
    bundle_raw = subprocess.check_output(
        ["terraform", "-chdir", str(terraform_dir), "output", "-json", "config_bundle"],
        text=True,
    )
except subprocess.CalledProcessError as exc:
    raise SystemExit(
        "Failed to read Terraform outputs. Run `terraform apply` in infrastructure to populate state."
    ) from exc

bundle = json.loads(bundle_raw)
if "value" in bundle:
    bundle = bundle["value"]

services_config = config.get("services", {})
postgres_enabled = services_config.get("postgres", True)
traefik_enabled = services_config.get("traefik", False)
n8n_enabled = services_config.get("n8n", False)
wazuh_enabled = services_config.get("wazuh", False)

backend_env_internal = bundle["backend"]["env"]
backend_env_public = bundle["backend"]["env_public"]
backend_env = backend_env_internal if postgres_enabled else backend_env_public

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
