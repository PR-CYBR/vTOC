#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
export DATABASE_URL="${DATABASE_URL_TOC_S2:-postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s2}"

pushd "$ROOT_DIR/backend" >/dev/null
alembic upgrade head
popd >/dev/null
