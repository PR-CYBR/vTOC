#!/usr/bin/env bash

set -euo pipefail

_version_ge() {
  local current="$1"
  local required="$2"

  if [[ "$current" == "$required" ]]; then
    return 0
  fi

  local sorted
  sorted=$(printf '%s\n%s\n' "$current" "$required" | sort -V | head -n1)
  [[ "$sorted" == "$required" ]]
}

_extract_version() {
  local text="$1"
  grep -oE '[0-9]+(\.[0-9]+)+' <<<"$text" | head -n1
}

_check_docker_compose() {
  local min_version="$1"
  local install_url="$2"
  local current_version=""
  local output=""

  if command -v docker-compose >/dev/null 2>&1; then
    output=$(docker-compose version --short 2>/dev/null || docker-compose version 2>/dev/null || true)
  else
    if docker compose version >/dev/null 2>&1; then
      output=$(docker compose version 2>/dev/null || true)
    fi
  fi

  if [[ -z "$output" ]]; then
    printf '\nMissing dependency: Docker Compose\n' >&2
    printf '  Install instructions: %s\n' "$install_url" >&2
    return 1
  fi

  current_version=$(_extract_version "$output")
  if [[ -z "$current_version" ]]; then
    printf '\nUnable to determine Docker Compose version.\n' >&2
    printf '  Verify your installation: %s\n' "$install_url" >&2
    return 1
  fi

  if ! _version_ge "$current_version" "$min_version"; then
    printf '\nUnsupported Docker Compose version detected (%s).\n' "$current_version" >&2
    printf '  Minimum required version: %s\n' "$min_version" >&2
    printf '  Upgrade instructions: %s\n' "$install_url" >&2
    return 1
  fi

  return 0
}

check_prereqs() {
  if [[ $# -eq 0 ]]; then
    return 0
  fi

  local missing=0

  for requirement in "$@"; do
    IFS='|' read -r command min_version install_url <<<"$requirement"
    local display_name="$command"

    case "$command" in
      docker-compose)
        if ! _check_docker_compose "$min_version" "$install_url"; then
          missing=$((missing + 1))
        fi
        continue
        ;;
    esac

    if ! command -v "$command" >/dev/null 2>&1; then
      printf '\nMissing dependency: %s\n' "$display_name" >&2
      printf '  Install instructions: %s\n' "$install_url" >&2
      missing=$((missing + 1))
      continue
    fi

    if [[ -z "$min_version" ]]; then
      continue
    fi

    local version_output
    case "$command" in
      docker)
        version_output=$(docker --version 2>/dev/null || true)
        ;;
      pnpm)
        version_output=$(pnpm --version 2>/dev/null || true)
        ;;
      python3)
        version_output=$(python3 --version 2>/dev/null || true)
        ;;
      terraform)
        version_output=$(terraform version 2>/dev/null || true)
        ;;
      ansible-playbook)
        version_output=$(ansible-playbook --version 2>/dev/null || true)
        ;;
      *)
        version_output=$("$command" --version 2>/dev/null || true)
        ;;
    esac

    local current_version
    current_version=$(_extract_version "$version_output")

    if [[ -z "$current_version" ]]; then
      printf '\nUnable to determine %s version.\n' "$display_name" >&2
      printf '  Verify your installation: %s\n' "$install_url" >&2
      missing=$((missing + 1))
      continue
    fi

    if ! _version_ge "$current_version" "$min_version"; then
      printf '\nUnsupported %s version detected (%s).\n' "$display_name" "$current_version" >&2
      printf '  Minimum required version: %s\n' "$min_version" >&2
      printf '  Upgrade instructions: %s\n' "$install_url" >&2
      missing=$((missing + 1))
    fi
  done

  if (( missing > 0 )); then
    printf '\nResolve the missing prerequisites above and re-run the setup command.\n' >&2
    return 1
  fi

  return 0
}
