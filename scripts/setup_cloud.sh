#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/prereqs.sh
source "$SCRIPT_DIR/lib/prereqs.sh"

ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TERRAFORM_DIR="$ROOT_DIR/infrastructure/terraform"
CONFIG_JSON="${VTOC_CONFIG_JSON:-{}}"
APPLY="${VTOC_SETUP_APPLY:-false}"
CONFIGURE="${VTOC_SETUP_CONFIGURE:-false}"

requirements=(
  "python3|3.9.0|https://www.python.org/downloads/"
  "terraform|1.5.0|https://developer.hashicorp.com/terraform/downloads"
)

if [[ "$CONFIGURE" == "true" ]]; then
  requirements+=(
    "ansible-playbook|2.14.0|https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html"
  )
fi

check_prereqs "${requirements[@]}"

export VTOC_CONFIG_JSON="$CONFIG_JSON"

args=(
  --output-dir "$ROOT_DIR/infra"
  --terraform-source "$TERRAFORM_DIR"
  --fallback-bundle "$ROOT_DIR/scripts/defaults/config_bundle.local.json"
)

if [[ "$APPLY" == "true" ]]; then
  args+=(--apply)
fi

if [[ "$CONFIGURE" == "true" ]]; then
  args+=(--configure)
fi

python -m scripts.bootstrap.cloud "${args[@]}"
