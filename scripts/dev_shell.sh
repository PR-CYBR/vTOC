#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/.devcontainer/docker-compose.devcontainer.yml"
SERVICE_NAME="devcontainer"

usage() {
  cat <<'USAGE'
Launch the vTOC developer container locally.

Usage: dev_shell.sh [--setup] [--no-database] [--] [command]

Options:
  --setup         Run "make setup-local" inside the container before starting an interactive shell.
  --no-database   Do not start the bundled Postgres service.
  -h, --help      Show this help text.
  --              Treat the remaining arguments as the command to run inside the container.

Examples:
  # Start an interactive shell with the default toolchain
  ./scripts/dev_shell.sh

  # Run the bootstrap workflow and keep the shell open afterwards
  ./scripts/dev_shell.sh --setup

  # Execute a one-off command without the Postgres sidecar
  ./scripts/dev_shell.sh --no-database -- pnpm --dir frontend test
USAGE
}

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Devcontainer compose file missing at $COMPOSE_FILE" >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_BIN=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN=(docker-compose)
else
  echo "Docker Compose (plugin or standalone) is required to launch the developer container." >&2
  exit 1
fi

COMPOSE=(${COMPOSE_BIN[@]})
COMPOSE+=(-f "$COMPOSE_FILE")
SETUP="false"
START_DATABASE="true"
COMMAND=("bash")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --setup)
      SETUP="true"
      shift
      ;;
    --no-database)
      START_DATABASE="false"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      COMMAND=("$@")
      break
      ;;
    *)
      COMMAND=("$@")
      break
      ;;
  esac
done

if [[ "$START_DATABASE" == "true" ]]; then
  "${COMPOSE[@]}" up -d database >/dev/null
fi

RUN_ARGS=("${COMPOSE[@]}" run --rm --service-ports "$SERVICE_NAME")

if [[ "$SETUP" == "true" ]]; then
  "${RUN_ARGS[@]}" bash -lc "make setup-local"
fi

exec "${RUN_ARGS[@]}" "${COMMAND[@]}"
