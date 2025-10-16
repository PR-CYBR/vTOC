#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GHCR_USERNAME:-}" ]]; then
  echo "GHCR_USERNAME is required" >&2
  exit 1
fi

if [[ -z "${GHCR_TOKEN:-}" ]]; then
  echo "GHCR_TOKEN is required" >&2
  exit 1
fi

# Construct Docker auth config for Fly remote builder
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

IMAGE_TAG=${TAG:-latest}

echo "Deploying ghcr.io/pr-cybr/vtoc/backend:${IMAGE_TAG} to Fly.io"
exec flyctl deploy --image "ghcr.io/pr-cybr/vtoc/backend:${IMAGE_TAG}" --remote-only "$@"
