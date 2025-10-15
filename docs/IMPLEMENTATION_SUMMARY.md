# vTOC Implementation Summary

This summary captures the major components that make up the ChatKit-augmented vTOC platform. Use it alongside the
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md) reference for deeper dives.

## Backend API (FastAPI)

- Location: `backend/`
- Exposes REST routers for telemetry, stations, and mission management (`/api/v1/*`).
- Hosts `/api/v1/chatkit/webhook` for ChatKit event ingestion and `/api/v1/agentkit/runs` for internal job tracking.
- Uses SQLAlchemy models synced via Alembic migrations (`alembic/`).
- Integrates with ChatKit and AgentKit using environment variables documented in [`README.md`](../README.md).
- Provides role-aware dependency overrides so that each station resolves its own Postgres database.

## Frontend application (Vite + React + TypeScript)

- Location: `frontend/`
- Offers dashboards for Operations, Intelligence, and Logistics stations with role-specific panels.
- Includes a ChatKit console sidebar that streams mission threads and AgentKit status updates via the API.
- Consumes the backend through `src/services/api.ts` and honors environment variables from `.env.station`.
- Tested via Vitest (`pnpm --dir frontend test`).

## Telemetry ingestion layer

- Location: `agents/` and `backend/app/telemetry`.
- `agents/scraper` pulls from ADS-B, AIS, APRS, TLE, RTL-SDR, Meshtastic, GPS, and custom connectors defined in
  [`docs/TELEMETRY_CONNECTORS.md`](TELEMETRY_CONNECTORS.md).
- AgentKit playbooks reuse the same connector implementations through `agents/lib/connector_runner.py`.
- Telemetry events persist to station-specific Postgres schemas and can be broadcast to ChatKit threads using
  `TELEMETRY_BROADCAST_URL`.

## Chat orchestration (ChatKit + AgentKit)

- ChatKit organizes channels per station and threads per mission.
- Backend webhook normalizes messages, applies station role policies, and schedules AgentKit runs.
- AgentKit executes playbooks declared in `agents/config/agentkit.yml`, publishing summaries back to ChatKit and the mission log.
- `scripts/setup.sh` provisions sandbox channels and stores their IDs inside `.env.station`.

## Infrastructure & automation

- Makefile targets (`setup-local`, `setup-container`, `setup-cloud`, `compose-up`, `compose-down`) provide consistent workflows.
- `docs/DEPLOYMENT.md` covers Docker Compose, Swarm, Fly.io (`live` branch), and Terraform snippets for multi-station Postgres.
- GitHub Actions pipelines build and push container images to GHCR.

## Documentation & change management

- Quick start, deployment, and architecture docs are synchronized with ChatKit/AgentKit requirements.
- [`docs/CHANGELOG.md`](CHANGELOG.md) describes the migration path from the pre-ChatKit release.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) outlines development standards and testing expectations.
