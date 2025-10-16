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

export ROOT_DIR TERRAFORM_DIR

python - <<'PY'
import subprocess
from pathlib import Path
import os
import sys

root_dir = Path(os.environ["ROOT_DIR"])
terraform_dir = Path(os.environ["TERRAFORM_DIR"])

try:
    frontend_env = subprocess.check_output(
        ["terraform", "-chdir", str(terraform_dir), "output", "-raw", "frontend_env_file"],
        text=True,
    )
except subprocess.CalledProcessError as exc:
    print(
        "Failed to read Terraform outputs. Run `terraform apply` in infrastructure/terraform to populate state.",
        file=sys.stderr,
    )
    raise SystemExit(exc.returncode) from exc

frontend_dir = root_dir / "frontend"
(frontend_dir / ".env.local").write_text(frontend_env)
PY

(cd "$ROOT_DIR/frontend" && pnpm install --frozen-lockfile)
(cd "$ROOT_DIR/frontend" && pnpm build)

printf 'Local mode complete. Start the dev server with "pnpm --dir frontend dev".\n'
