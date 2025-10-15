#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"

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
ENV

(cd "$ROOT_DIR/frontend" && pnpm build)

printf 'Local mode complete. Start the dev server with "pnpm --dir frontend dev".\n'
