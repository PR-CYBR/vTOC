#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_FILE="$ROOT_DIR/docker-compose.generated.yml"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"
APPLY="${VTOC_SETUP_APPLY:-false}"
USE_REMOTE_IMAGES="${VTOC_USE_REMOTE_IMAGES:-false}"
PULL_IMAGES="false"
IMAGE_TAG="${VTOC_IMAGE_TAG:-}" 
IMAGE_PREFIX="${VTOC_IMAGE_PREFIX:-}"

usage() {
  cat <<'USAGE'
Usage: setup_container.sh [--pull] [--image-tag <tag>] [--image-prefix <registry/repo>] [--output <file>]

Options:
  --pull             Pull published images for backend/frontend/scraper and reference them in the manifest.
  --image-tag        Image tag to use when referencing published images (default: github.sha when available).
  --image-prefix     Override the image prefix (default: ghcr.io/<github_repository> lowercased).
  --output           Path to write the generated compose file (default: docker-compose.generated.yml).
  -h, --help         Show this help message.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      PULL_IMAGES="true"
      USE_REMOTE_IMAGES="true"
      shift
      ;;
    --image-tag)
      IMAGE_TAG="$2"
      USE_REMOTE_IMAGES="true"
      shift 2
      ;;
    --image-prefix)
      IMAGE_PREFIX="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
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

if [[ -z "$IMAGE_TAG" ]]; then
  IMAGE_TAG="${GITHUB_SHA:-latest}"
fi

if [[ -z "$IMAGE_PREFIX" ]]; then
  IMAGE_PREFIX_BASE="${GITHUB_REPOSITORY:-pr-cybr/vtoc}"
  IMAGE_PREFIX="ghcr.io/$(echo "$IMAGE_PREFIX_BASE" | tr '[:upper:]' '[:lower:]')"
fi

export ROOT_DIR OUTPUT_FILE CONFIG_JSON USE_REMOTE_IMAGES IMAGE_PREFIX IMAGE_TAG

python - <<'PY'
import json
from pathlib import Path
import os

root_dir = Path(os.environ['ROOT_DIR'])
output_file = Path(os.environ['OUTPUT_FILE'])
config_json = os.environ.get('CONFIG_JSON', '{}')
config = json.loads(config_json)
services_config = config.get('services', {})
use_remote_images = os.environ.get('USE_REMOTE_IMAGES', 'false').lower() == 'true'
image_prefix = os.environ.get('IMAGE_PREFIX', '')
image_tag = os.environ.get('IMAGE_TAG', 'latest')

postgres_enabled = services_config.get('postgres', True)
traefik_enabled = services_config.get('traefik', False)
n8n_enabled = services_config.get('n8n', False)
wazuh_enabled = services_config.get('wazuh', False)

compose = {
    'version': '3.8',
    'services': {
        'backend': {
            'build': {'context': './backend'},
            'ports': ['8080:8080'],
            'environment': {
                'DATABASE_URL': 'postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc',
                'DATABASE_URL_TOC_S1': 'postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc?options=-csearch_path%3Dtoc_s1',
                'DATABASE_URL_TOC_S2': 'postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc?options=-csearch_path%3Dtoc_s2',
                'DATABASE_URL_TOC_S3': 'postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc?options=-csearch_path%3Dtoc_s3',
                'DATABASE_URL_TOC_S4': 'postgresql+psycopg2://vtoc:vtocpass@database:5432/vtoc?options=-csearch_path%3Dtoc_s4',
            },
            'depends_on': ['database'],
        },
        'frontend': {
            'build': {'context': './frontend'},
            'ports': ['8081:8081'],
            'depends_on': ['backend'],
        },
        'scraper': {
            'build': {'context': './agents/scraper'},
            'environment': {'BACKEND_BASE_URL': 'http://backend:8080'},
            'depends_on': ['backend'],
        },
    },
    'networks': {'default': {'driver': 'bridge'}},
}

if use_remote_images and image_prefix:
    for service in ('backend', 'frontend', 'scraper'):
        compose['services'][service]['image'] = f"{image_prefix}/{service}:{image_tag}"
        compose['services'][service].pop('build', None)

if postgres_enabled:
    compose.setdefault('volumes', {})['postgres_data'] = {}
    compose['services']['database'] = {
        'image': 'postgres:15-alpine',
        'environment': {
            'POSTGRES_DB': 'vtoc',
            'POSTGRES_USER': 'vtoc',
            'POSTGRES_PASSWORD': 'vtocpass',
        },
        'volumes': [
            'postgres_data:/var/lib/postgresql/data',
            './database/init:/docker-entrypoint-initdb.d'
        ],
        'ports': ['5432:5432'],
    }
else:
    compose['services']['backend']['environment']['DATABASE_URL'] = os.environ.get(
        'DATABASE_URL', ''
    )
    compose['services']['backend'].pop('depends_on', None)

if traefik_enabled:
    compose['services']['traefik'] = {
        'image': 'traefik:v2.11',
        'command': [
            '--providers.docker=true',
            '--providers.docker.exposedbydefault=false',
            '--entrypoints.web.address=:80',
        ],
        'ports': ['80:80'],
        'volumes': ['/var/run/docker.sock:/var/run/docker.sock:ro'],
    }
    compose['services']['backend']['labels'] = [
        'traefik.enable=true',
        'traefik.http.routers.backend.rule=Host(`api.vtoc.local`)',
        'traefik.http.services.backend.loadbalancer.server.port=8080',
    ]
    compose['services']['frontend']['labels'] = [
        'traefik.enable=true',
        'traefik.http.routers.frontend.rule=Host(`vtoc.local`)',
        'traefik.http.services.frontend.loadbalancer.server.port=8081',
    ]

if n8n_enabled:
    compose['services']['n8n'] = {
        'image': 'n8nio/n8n:latest',
        'ports': ['5678:5678'],
    }

if wazuh_enabled:
    compose['services']['wazuh-manager'] = {
        'image': 'wazuh/wazuh-manager:4.7.5',
        'ports': ['55000:55000'],
    }


def dump_yaml(value, indent=0):
    spaces = '  ' * indent
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
output_file.write_text('\n'.join(lines) + '\n')
PY

if [[ "$PULL_IMAGES" == "true" ]]; then
  for service in backend frontend scraper; do
    docker pull "${IMAGE_PREFIX}/${service}:${IMAGE_TAG}"
  done
fi

if [[ "$APPLY" == "true" ]]; then
  docker compose -f "$OUTPUT_FILE" up -d
else
  printf 'Generated %s. Run `docker compose -f %s up -d` to start containers.\n' "$OUTPUT_FILE" "$OUTPUT_FILE"
fi
