#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TERRAFORM_DIR="$ROOT_DIR/infrastructure"

terraform -chdir="$TERRAFORM_DIR" init -input=false >/dev/null

if ! FLY_SECRETS_PAYLOAD=$(terraform -chdir="$TERRAFORM_DIR" output -raw fly_secrets_env 2>/dev/null); then
  echo "Failed to read fly_secrets_env from Terraform outputs. Run \`terraform apply\` in infrastructure to populate state." >&2
  exit 1
fi

if ! RUNTIME_JSON=$(terraform -chdir="$TERRAFORM_DIR" output -json fly_runtime_credentials 2>/dev/null); then
  echo "Failed to read fly_runtime_credentials from Terraform outputs. Run \`terraform apply\` in infrastructure to populate state." >&2
  exit 1
fi

export RUNTIME_JSON
runtime_exports=$(python - <<'PY'
import json
import os
import shlex

data = json.loads(os.environ["RUNTIME_JSON"])
if "value" in data:
    data = data["value"]

pairs = [
    ("app_name", "FLY_APP_NAME"),
    ("api_token", "FLY_API_TOKEN"),
    ("ghcr_username", "GHCR_USERNAME"),
    ("ghcr_token", "GHCR_TOKEN"),
    ("backend_image", "BACKEND_IMAGE_REPOSITORY"),
    ("frontend_image", "FRONTEND_IMAGE_REPOSITORY"),
    ("scraper_image", "SCRAPER_IMAGE_REPOSITORY"),
]

for key, env_key in pairs:
    existing = os.environ.get(env_key)
    value = existing if existing is not None and existing != "" else str(data.get(key, ""))
    print(f"export {env_key}={shlex.quote(value)}")
PY
)
unset RUNTIME_JSON

eval "$runtime_exports"

if [[ -z "${GHCR_USERNAME:-}" ]]; then
  echo "GHCR_USERNAME could not be resolved from Terraform outputs." >&2
  exit 1
fi

if [[ -z "${GHCR_TOKEN:-}" ]]; then
  echo "GHCR_TOKEN could not be resolved from Terraform outputs." >&2
  exit 1
fi

if [[ -z "${FLY_API_TOKEN:-}" ]]; then
  echo "FLY_API_TOKEN could not be resolved from Terraform outputs." >&2
  exit 1
fi

DOCKER_CONFIG_DIR=$(mktemp -d)
trap 'rm -rf "$DOCKER_CONFIG_DIR"' EXIT

cat >"$DOCKER_CONFIG_DIR/config.json" <<JSON
{
  "auths": {
    "ghcr.io": {
      "auth": "$(printf '%s:%s' "$GHCR_USERNAME" "$GHCR_TOKEN" | base64 | tr -d '\n')"
    }
  }
}
JSON

export DOCKER_CONFIG="$DOCKER_CONFIG_DIR"
export DOCKER_AUTH_CONFIG="$(cat "$DOCKER_CONFIG_DIR/config.json")"

IMAGE_TAG="${TAG:-latest}"

printf '%s' "$FLY_SECRETS_PAYLOAD" | flyctl secrets import --app "$FLY_APP_NAME" --stage

echo "Deploying ${BACKEND_IMAGE_REPOSITORY}:${IMAGE_TAG} to Fly.io (app: ${FLY_APP_NAME})"
exec flyctl deploy \
  --app "$FLY_APP_NAME" \
  --image "${BACKEND_IMAGE_REPOSITORY}:${IMAGE_TAG}" \
  --config "$ROOT_DIR/fly.toml" \
  --remote-only "$@"
