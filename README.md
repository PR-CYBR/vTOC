# vTOC Platform

vTOC is a virtual tactical operations center that ships with a FastAPI backend, a map-first Vite frontend, and automation agents for ingesting telemetry. The project now supports three deployment modes through a universal setup script and provides container images for local development, Swarm, and Fly.io.

![CI](https://github.com/PR-CYBR/vTOC/actions/workflows/ci.yml/badge.svg) ![Preview Deploy](https://github.com/PR-CYBR/vTOC/actions/workflows/preview-deploy.yml/badge.svg)

## Quick start

```bash
make setup-local
pnpm --dir frontend dev
```

The backend exposes `http://localhost:8080/healthz` and the frontend renders on `http://localhost:5173` during development (or `8081` when using the containerized stack).

## Deployment modes

| Mode       | Command                               | Description |
|------------|----------------------------------------|-------------|
| Local      | `make setup-local`                     | Installs dependencies, writes `.env.local`, and runs frontend build validation. |
| Container  | `make setup-container`                 | Generates `docker-compose.generated.yml` (respecting optional services from the JSON schema) and starts the stack. |
| Cloud      | `make setup-cloud`                     | Produces Terraform and Ansible scaffolding in `infra/` for infrastructure provisioning. |

Supply configuration through `--config path.json` or `--config-json '{...}'`. See [`scripts/inputs.schema.json`](scripts/inputs.schema.json) for the accepted structure.

Codex CLI is detected automatically: if the `codex` binary exists, the setup scripts use `codex interpolate` for variable expansion; otherwise the scripts fall back to standard Bash behaviour.

## Containers and orchestration

* `docker-compose.yml` — developer stack (Postgres, FastAPI backend, Vite frontend via nginx, telemetry scraper)
* `docker-stack.yml` — Docker Swarm with Traefik routing (`vtoc.local` / `api.vtoc.local`) and optional integrations (ZeroTier, Tailscale, MediaMTX, TAK Server)
* `fly.toml` — Fly.io deployment descriptor for the backend container

Images are built and pushed to GHCR via GitHub Actions as part of the [`ci.yml`](.github/workflows/ci.yml) workflow:

- `ghcr.io/<repo>/frontend` (Vite static bundle served by nginx)
- `ghcr.io/<repo>/backend` (FastAPI + Uvicorn on port 8080)
- `ghcr.io/<repo>/scraper` (RSS/HTML telemetry agent)

A Fly.io dispatch workflow (`fly-deploy.yml`) deploys the backend using the prebuilt image when triggered manually or when tags matching `v*` are pushed.

## Frontend

The Vite/React frontend consumes the backend via `frontend/src/services/api.ts` and presents a Leaflet-powered operational map with a collapsible Intel panel. Environment configuration lives in [`frontend/.env.example`](frontend/.env.example) and is propagated through the setup scripts.

Key scripts:

```bash
pnpm --dir frontend dev     # local dev server on 5173
pnpm --dir frontend build   # generate production bundle
pnpm --dir frontend test    # run vitest suite in CI mode
```

## Backend

The FastAPI backend (`backend/app`) provides:

* `/healthz` — health probe
* `/api/v1/telemetry/sources` — CRUD for telemetry sources
* `/api/v1/telemetry/events` — Telemetry events with optional geospatial metadata

Database connectivity is supplied through `DATABASE_URL`. SQLAlchemy models and Alembic migrations live under `backend/app` and `alembic/`. Run migrations with:

```bash
alembic upgrade head
```

## Telemetry scraper

`agents/scraper` reads feeds from `config.yaml` and posts normalized telemetry to the backend. It supports RSS feeds and optional HTML selectors via Selectolax. Run locally with `make scraper-run` or containerize via the provided Dockerfile.

## Documentation

Additional deployment guidance is available in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) including Compose, Swarm, Fly.io, and sample `inputs.json` files for each setup mode. For production status updates and release notes, subscribe to the GitHub Discussion **Deployment Strategy: live branch** (link in the deployment guide) so you know when `live` has been updated and whether a rollback or hotfix is in flight.
