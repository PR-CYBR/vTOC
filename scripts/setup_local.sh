#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/prereqs.sh
source "$SCRIPT_DIR/lib/prereqs.sh"

ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TERRAFORM_DIR="$ROOT_DIR/infrastructure/terraform"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"

check_prereqs \
  "pnpm|8.6.0|https://pnpm.io/installation" \
  "terraform|1.5.0|https://developer.hashicorp.com/terraform/downloads"

printf 'Running local setup with configuration: %s\n' "$CONFIG_JSON"

if command -v codex >/dev/null 2>&1; then
  codex note "Executing local mode setup"
fi

terraform -chdir="$TERRAFORM_DIR" init -input=false >/dev/null

python -m scripts.automation.local_bootstrap

(cd "$ROOT_DIR/frontend" && pnpm install --frozen-lockfile)
(cd "$ROOT_DIR/frontend" && pnpm build)

printf 'Local mode complete. Start the dev server with "pnpm --dir frontend dev".\n'
