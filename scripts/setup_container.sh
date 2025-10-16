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
OUTPUT_FILE="$ROOT_DIR/docker-compose.generated.yml"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"
APPLY="${VTOC_SETUP_APPLY:-false}"
IMAGE_TAG="${VTOC_IMAGE_TAG:-main}"
IMAGE_REPO="${VTOC_IMAGE_REPO:-ghcr.io/pr-cybr/vtoc}"
USE_BUILD_LOCAL="${VTOC_BUILD_LOCAL:-false}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      USE_BUILD_LOCAL="false"
      shift
      ;;
    --image-tag)
      if [[ $# -lt 2 ]]; then
        echo "--image-tag requires a value" >&2
        exit 1
      fi
      IMAGE_TAG="$2"
      USE_BUILD_LOCAL="false"
      shift 2
      ;;
    --build-local)
      USE_BUILD_LOCAL="true"
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

export ROOT_DIR OUTPUT_FILE CONFIG_JSON IMAGE_TAG IMAGE_REPO USE_BUILD_LOCAL

python - <<'PY'
import json
from pathlib import Path
import os

root_dir = Path(os.environ['ROOT_DIR'])
output_file = Path(os.environ['OUTPUT_FILE'])
config_json = os.environ.get('CONFIG_JSON', '{}')
config = json.loads(config_json)
image_repo = os.environ.get('IMAGE_REPO', 'ghcr.io/pr-cybr/vtoc')
image_tag = os.environ.get('IMAGE_TAG', 'main')
use_build_local = os.environ.get('USE_BUILD_LOCAL', 'false').lower() == 'true'
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
            'ports': ['8081:8081'],
            'depends_on': ['backend'],
        },
        'scraper': {
            'environment': {'BACKEND_BASE_URL': 'http://backend:8080'},
            'depends_on': ['backend'],
        },
    },
    'networks': {'default': {'driver': 'bridge'}},
}

if not use_build_local:
    compose['services']['backend']['image'] = f"{image_repo}/backend:{image_tag}"
    compose['services']['backend']['pull_policy'] = 'always'
    compose['services']['frontend']['image'] = f"{image_repo}/frontend:{image_tag}"
    compose['services']['frontend']['pull_policy'] = 'always'
    compose['services']['scraper']['image'] = f"{image_repo}/scraper:{image_tag}"
    compose['services']['scraper']['pull_policy'] = 'always'
else:
    compose['services']['backend']['build'] = {'context': './backend'}
    compose['services']['frontend']['build'] = {'context': './frontend'}
    compose['services']['scraper']['build'] = {'context': './agents/scraper'}

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
