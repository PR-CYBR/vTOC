#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/prereqs.sh
source "$SCRIPT_DIR/lib/prereqs.sh"

ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_JSON="${VTOC_CONFIG_JSON:-}" 

check_prereqs \
  "pnpm|8.6.0|https://pnpm.io/installation"

if command -v codex >/dev/null 2>&1; then
  codex note "Executing local mode setup"
fi

args=("--terraform-dir" "$ROOT_DIR/infrastructure/terraform")
if [[ -n "$CONFIG_JSON" ]]; then
  args+=("--config-json" "$CONFIG_JSON")
fi

python -m scripts.bootstrap.local "${args[@]}"
