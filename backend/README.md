# vTOC Backend

The backend is a FastAPI service that exposes telemetry, station, and ChatKit/AgentKit orchestration endpoints. It is designed to
run either alongside the full stack (`make setup-container`) or as a standalone service for development.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc_ops"
export POSTGRES_STATION_ROLE="ops"
export CHATKIT_API_KEY="..." CHATKIT_ORG_ID="..."
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

To reuse the generated configuration from the setup script, source `.env.local` and `.env.station`:

```bash
set -a
source ../.env.local
source ../.env.station
set +a
```

## Alembic migrations

The shared Alembic configuration lives at the project root and supports per-role migrations.

```bash
# Upgrade schema for the active POSTGRES_STATION_ROLE
alembic upgrade head

# Create a new revision
alembic revision --autogenerate -m "describe changes"
```

For multi-station deployments set `POSTGRES_STATION_ROLE` before invoking Alembic so the correct database URL is resolved.

## Tests & tooling

```bash
make backend-test  # runs pytest in quiet mode
```

Additional helpful commands:

```bash
uvicorn app.main:app --reload  # auto-reload during development
pytest -k telemetry --maxfail=1
```

Refer to [`CONTRIBUTING.md`](../CONTRIBUTING.md) for coding standards and review expectations.
