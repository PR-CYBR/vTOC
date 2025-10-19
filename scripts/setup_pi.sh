#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: setup_pi.sh [--pull] [--image-tag <tag>] [--build-local]

Options mirror setup_container.sh but apply Raspberry Pi defaults.
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTAINER_SETUP="$SCRIPT_DIR/setup_container.sh"
if [[ ! -x "$CONTAINER_SETUP" ]]; then
  echo "setup_container.sh is missing or not executable" >&2
  exit 1
fi

for arg in "$@"; do
  case "$arg" in
    --help|-h)
      usage
      exit 0
      ;;
  esac
done

TRANSFORMED_CONFIG="$(python - <<'PY'
import json
import os
import sys

raw = os.environ.get("VTOC_CONFIG_JSON", "{}")
raw = raw.strip() or "{}"
try:
    data = json.loads(raw)
except json.JSONDecodeError as exc:
    sys.stderr.write(f"Invalid VTOC_CONFIG_JSON payload: {exc}\n")
    sys.exit(1)

data["hardwareProfile"] = "pi"
services = data.setdefault("services", {})
for key in ("traefik", "postgres", "n8n", "wazuh", "adsb", "gps", "h4m"):
    services[key] = False

bundle = data.setdefault("configBundle", {})
backend = bundle.setdefault("backend", {})
backend.setdefault("env", {})
env_public = backend.setdefault("env_public", {})
env_public.setdefault("DATABASE_URL", "sqlite:///var/lib/vtoc/vtoc.db")
env_public.setdefault("SUPABASE_DB_URL", "")
env_public.setdefault("SUPABASE_URL", "")
env_public.setdefault("SUPABASE_PROJECT_REF", "")
env_public.setdefault("SUPABASE_SERVICE_ROLE_KEY", "")
env_public.setdefault("SUPABASE_ANON_KEY", "")
env_public.setdefault("SUPABASE_JWT_SECRET", "")

scraper = bundle.setdefault("scraper", {})
scraper.setdefault("env", {"BACKEND_BASE_URL": "http://backend:8080"})

json.dump(data, sys.stdout)
PY
)"

export VTOC_CONFIG_JSON="$TRANSFORMED_CONFIG"

if [[ -z "${VTOC_COMPOSE_FILENAME:-}" ]]; then
  export VTOC_COMPOSE_FILENAME="docker-compose.pi.yml"
fi

if [[ -z "${VTOC_COMPOSE_PLATFORM:-}" ]]; then
  export VTOC_COMPOSE_PLATFORM="linux/arm64"
fi

if [[ -z "${VTOC_IMAGE_TAG:-}" ]]; then
  export VTOC_IMAGE_TAG="main-arm64"
fi

exec "$CONTAINER_SETUP" "$@"
