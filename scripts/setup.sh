#!/usr/bin/env bash
set -euo pipefail

MODE="${VTOC_SETUP_MODE:-}"
CONFIG_PATH=""
CONFIG_JSON_ARG=""
APPLY="false"
CONFIGURE="false"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  cat <<USAGE
Usage: $0 [--mode local|container|cloud] [--config path.json] [--config-json '{...}'] [--apply] [--configure]

Flags:
  --mode           Deployment mode to run (local, container, cloud)
  --config         Path to a JSON configuration file
  --config-json    Inline JSON configuration string
  --apply          Execute infrastructure changes automatically when supported
  --configure      Run configuration management automatically when supported
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --config-json)
      CONFIG_JSON_ARG="$2"
      shift 2
      ;;
    --apply)
      APPLY="true"
      shift
      ;;
    --configure)
      CONFIGURE="true"
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

if [[ -z "${MODE}" ]]; then
  MODE="local"
fi

load_config() {
  if [[ -n "$CONFIG_JSON_ARG" ]]; then
    echo "$CONFIG_JSON_ARG"
    return
  fi

  if [[ -n "$CONFIG_PATH" ]]; then
    if [[ ! -f "$CONFIG_PATH" ]]; then
      echo "Configuration file not found: $CONFIG_PATH" >&2
      exit 1
    fi
    cat "$CONFIG_PATH"
    return
  fi

  if [[ -n "${VTOC_CONFIG_JSON:-}" ]]; then
    echo "$VTOC_CONFIG_JSON"
    return
  fi

  if [[ -t 0 ]]; then
    read -r -p "Project name [vtoc]: " project_name
    project_name=${project_name:-vtoc}
    read -r -p "Include Traefik? (y/N): " include_traefik
    read -r -p "Include Postgres? (Y/n): " include_postgres
    read -r -p "Include n8n? (y/N): " include_n8n
    read -r -p "Include Wazuh? (y/N): " include_wazuh
    python - <<PY
import json
print(json.dumps({
    "projectName": "${project_name}",
    "services": {
        "traefik": "${include_traefik,,}" in {"y", "yes"},
        "postgres": "${include_postgres,,}" not in {"n", "no"},
        "n8n": "${include_n8n,,}" in {"y", "yes"},
        "wazuh": "${include_wazuh,,}" in {"y", "yes"}
    }
}))
PY
    return
  fi

  cat <<'JSON'
{"projectName":"vtoc","services":{"traefik":false,"postgres":true,"n8n":false,"wazuh":false}}
JSON
}

CODEX_BIN=""
if command -v codex >/dev/null 2>&1; then
  CODEX_BIN="$(command -v codex)"
fi

expand_with_codex() {
  local input="$1"
  if [[ -n "$CODEX_BIN" ]]; then
    "$CODEX_BIN" interpolate "$input" 2>/dev/null || echo "$input"
  else
    echo "$input"
  fi
}

validate_config_payload() {
  local json_input="$1"
  if ! python "$SCRIPT_DIR/lib/config_validator.py" "$SCRIPT_DIR/inputs.schema.json" <<<"$json_input"; then
    echo "Configuration validation failed." >&2
    return 1
  fi
}

CONFIG_JSON=$(load_config)
CONFIG_JSON=$(expand_with_codex "$CONFIG_JSON")

if ! validate_config_payload "$CONFIG_JSON"; then
  exit 1
fi

export VTOC_CONFIG_JSON="$CONFIG_JSON"
export VTOC_SETUP_APPLY="$APPLY"
export VTOC_SETUP_CONFIGURE="$CONFIGURE"
MODE_SCRIPT="$SCRIPT_DIR/setup_${MODE}.sh"

if [[ ! -x "$MODE_SCRIPT" ]]; then
  echo "Unsupported mode: $MODE" >&2
  exit 1
fi

"$MODE_SCRIPT"
