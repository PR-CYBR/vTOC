#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/prereqs.sh
source "$SCRIPT_DIR/lib/prereqs.sh"

ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"

check_prereqs \
  "pnpm|8.6.0|https://pnpm.io/installation"

printf 'Running local setup with configuration: %s\n' "$CONFIG_JSON"

if command -v codex >/dev/null 2>&1; then
  codex note "Executing local mode setup"
fi

(cd "$ROOT_DIR/frontend" && pnpm install --frozen-lockfile)

cat <<ENV > "$ROOT_DIR/frontend/.env.local"
VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8080}
VITE_MAP_TILES_URL=${VITE_MAP_TILES_URL:-https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png}
VITE_MAP_ATTRIBUTION=${VITE_MAP_ATTRIBUTION:-© OpenStreetMap contributors}
VITE_DEFAULT_DIV=${VITE_DEFAULT_DIV:-PR-SJU}
VITE_RSS_ENABLED=${VITE_RSS_ENABLED:-true}
VITE_CHAT_ENABLED=${VITE_CHAT_ENABLED:-true}
VITE_CHATKIT_WIDGET_URL=${VITE_CHATKIT_WIDGET_URL:-https://cdn.chatkit.example.com/widget.js}
VITE_CHATKIT_API_KEY=${VITE_CHATKIT_API_KEY:-}
VITE_CHATKIT_TELEMETRY_CHANNEL=${VITE_CHATKIT_TELEMETRY_CHANNEL:-vtoc-intel}
VITE_AGENTKIT_ORG_ID=${VITE_AGENTKIT_ORG_ID:-}
VITE_AGENTKIT_DEFAULT_STATION_CONTEXT=${VITE_AGENTKIT_DEFAULT_STATION_CONTEXT:-${VITE_DEFAULT_DIV:-PR-SJU}}
VITE_AGENTKIT_API_BASE_PATH=${VITE_AGENTKIT_API_BASE_PATH:-/api/v1/agent-actions}
ENV

(cd "$ROOT_DIR/frontend" && pnpm build)

printf 'Local mode complete. Start the dev server with "pnpm --dir frontend dev".\n'
