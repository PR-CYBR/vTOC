# vTOC Backend

This FastAPI backend exposes telemetry ingestion and query endpoints for the vTOC platform.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc"
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Alembic migrations

The repository includes a shared Alembic configuration at the project root.

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe changes"
```

Ensure the `DATABASE_URL` environment variable points at your Postgres instance before running Alembic commands.
