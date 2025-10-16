# Quick Start Guide

This guide helps station operators bring up vTOC with ChatKit + AgentKit integrations in five minutes. For a deeper architecture
walkthrough visit [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) and for production rollouts consult [`docs/DEPLOYMENT.md`](DEPLOYMENT.md).

## Prerequisites

Ensure you have:

- Docker 24+
- Docker Compose v2+
- Git
- `pnpm` (8+) for frontend development
- Access to ChatKit and AgentKit credentials with sandbox permissions

## Station roles

Every deployment declares at least one station role. The defaults ship with three profiles:

| Role | Env value | Purpose |
| --- | --- | --- |
| Operations | `ops` | Mission command, map overlays, dispatching tasks. |
| Intelligence | `intel` | Sensor fusion, telemetry enrichment, report drafting. |
| Logistics | `logistics` | Resource tracking, requisitions, sustainment plans. |

Set the desired role when prompted by the setup script or pre-fill it in a `--config` file under `stationRoles`.

## Installation steps

### 1. Clone repository

```bash
git clone https://github.com/PR-CYBR/vTOC.git
cd vTOC
```

### 2. Generate environment files

Use the unified bootstrap CLI to create `.env.local`, `.env.station`, and station-specific ChatKit channels.

```bash
python -m scripts.bootstrap_cli setup local
```

All Make targets remain as wrappers around this entry point, so existing automation can continue using `make setup-local`.

When prompted supply or confirm the following values:

- `POSTGRES_STATION_ROLE`
- `STATION_CALLSIGN`
- `CHATKIT_API_KEY` and `CHATKIT_ORG_ID`
- `AGENTKIT_CLIENT_ID` and `AGENTKIT_CLIENT_SECRET`
- Optional `TELEMETRY_BROADCAST_URL`

The script seeds `scripts/cache/` with the generated ChatKit channel IDs for reuse by other stations.

### 3. Start services

```bash
# Terminal 1 – backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8080

# Terminal 2 – frontend
pnpm --dir frontend dev
```

Or launch the containerized stack (includes Postgres) using the generated compose file:

```bash
python -m scripts.bootstrap_cli setup container --apply
python -m scripts.bootstrap_cli compose up
```

The generated compose file pulls prebuilt images from GHCR by default. To pin a specific tag, set `VTOC_IMAGE_TAG` (or pass
`--image-tag` to `scripts/setup_container.sh`). For example:

```bash
VTOC_IMAGE_TAG=main docker compose up
```

If you need to build services locally, regenerate the compose file with `./scripts/setup_container.sh --build-local` so the
`build:` blocks are reinstated.

### 4. Verify installation

```bash
# Check service status
docker compose -f docker-compose.generated.yml ps

# Backend health probe
curl http://localhost:8080/healthz

# ChatKit webhook echo test
curl -X POST http://localhost:8080/api/v1/chatkit/webhook -H 'Content-Type: application/json' \
  -d '{"channel":"'"${STATION_CALLSIGN}"'","text":"ping"}'
```

### 5. Access applications

- **Frontend**: http://localhost:5173 (dev) or http://localhost:8081 (compose)
- **API Docs**: http://localhost:8080/docs
- **ChatKit Console**: https://console.chatkit.example (replace with your tenant URL)
- **Traefik Dashboard (optional)**: http://localhost:8080 when Traefik is enabled in container mode

## First actions

1. **Register the station** via the UI: Settings → Stations → Register station. This stores `STATION_CALLSIGN` and ChatKit channel
   IDs in the backend.
2. **Create a mission** from the Operations pane. The mission timeline now includes ChatKit transcript references.
3. **Subscribe telemetry connectors** using the Telemetry admin page, or push sample data with `python -m scripts.bootstrap_cli scraper run` (or the `make scraper-run` alias).
4. **Trigger an AgentKit playbook** by posting `@agent run recon sweep` in the ChatKit channel. The backend webhook will launch
   the matching playbook and post a summary back to ChatKit.

## Common commands

### Bootstrap CLI commands

```bash
python -m scripts.bootstrap_cli --help                     # list all supported groups
python -m scripts.bootstrap_cli setup local                # generate env files and local configs
python -m scripts.bootstrap_cli setup container --apply    # synthesize docker-compose.generated.yml and role secrets
python -m scripts.bootstrap_cli compose up                 # start the generated compose stack
python -m scripts.bootstrap_cli compose down               # stop the stack and prune temp volumes
python -m scripts.bootstrap_cli backend test               # run FastAPI pytest suite
python -m scripts.bootstrap_cli frontend test              # run vitest suite (CI mode)
python -m scripts.bootstrap_cli scraper run                # execute telemetry scraper locally
```

Every command continues to have a matching Make target for teams that prefer `make` automation.

### Cleanup workflow

Run `python -m scripts.bootstrap_cli compose down` to stop containers created by the generated Compose file. To reset ChatKit bindings remove the
`.env.station` file and rerun `python -m scripts.bootstrap_cli setup local`; the script keeps cached channel IDs in `scripts/cache/` so you can choose to
reuse or recreate them.

## Troubleshooting

### Services will not start

```bash
# Inspect logs
docker compose -f docker-compose.generated.yml logs --tail 100

# Recreate stack
python -m scripts.bootstrap_cli compose down
python -m scripts.bootstrap_cli compose up
```

### ChatKit webhook fails with 401

Confirm `CHATKIT_API_KEY` and `CHATKIT_ORG_ID` in `.env.local`. Regenerate the key in the ChatKit console if the token has
expired.

### AgentKit playbook does not trigger

Verify that the station role in `.env.station` matches a configured playbook ID under `agents/config/agentkit.yml`. The backend
logs (see `backend/app/logging.py`) will include rejection reasons.

### Database connection errors

Make sure Postgres is reachable and that the generated `DATABASE_URL` references the correct hostname. For multi-station
setups, `python -m scripts.bootstrap_cli setup container --apply` (or `make setup-container`) adds suffixes such as `_ops`, `_intel`, `_logistics` to the default database names; confirm that
your local Postgres instance contains those schemas.

## Next steps

- Review [`docs/TELEMETRY_CONNECTORS.md`](TELEMETRY_CONNECTORS.md) for connector-specific options.
- Plan your deployment strategy with [`docs/DEPLOYMENT.md`](DEPLOYMENT.md).
- Track platform changes in [`docs/CHANGELOG.md`](CHANGELOG.md).
