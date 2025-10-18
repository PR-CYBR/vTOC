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
- A Supabase project (or operator-supplied credentials) for managed Postgres and authentication

The setup commands automatically verify these tools (and Python 3.9+) before running; missing dependencies trigger actionable
messages with installation links. On Windows, enable Corepack to install `pnpm` globally before invoking the setup scripts:

```powershell
corepack enable
corepack prepare pnpm@latest --activate
```

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

Interactive runs prompt for the required secrets. To automate the process (for example when driving the setup through an AI
assistant) supply the payload non-interactively via `--config-json` or `--config-json @path/to/config.json`. The JSON must match
[`scripts/inputs.schema.json`](../scripts/inputs.schema.json):

```bash
python -m scripts.bootstrap_cli setup local --config-json @- <<'JSON'
{
  "station": {
    "role": "ops",
    "callsign": "TOC-S1",
    "missionChannel": "ch_mission_123",
    "telemetryChannel": "ch_telemetry_123"
  },
  "chatkit": {
    "apiKey": "ck_live_xxx",
    "orgId": "org_abc123",
    "webhookSecret": "replace-me",
    "allowedTools": "intel-search,supply-lookup",
    "telemetryChannel": "ch_telemetry_123"
  },
  "agentkit": {
    "apiBaseUrl": "https://agentkit.example.com/api",
    "apiKey": "ak_live_xxx",
    "orgId": "org_abc123",
    "timeoutSeconds": 30,
    "defaultStationContext": "PR-SJU"
  },
  "supabase": {
    "url": "https://your-project.supabase.co",
    "projectRef": "your-project",
    "anonKey": "supabase-anon",
    "serviceRoleKey": "supabase-service-role"
  }
}
JSON
```

The CLI writes the merged secrets to `.env.local`, `.env.station`, and `frontend/.env.local` and echoes follow-up instructions in
both human-friendly and machine-readable formats. ChatKit channel IDs and station metadata are stored in `.env.station` so other
automation can reuse the values without rerunning the provisioning flow.

Supabase credentials can be generated from the [Supabase dashboard](https://supabase.com/dashboard). The bootstrap CLI persists
the anon key to both `.env.local` and `.env.station` for frontend use while keeping the service-role key scoped to backend
services.

### Environment variables

| Variable | Scope | Description |
| --- | --- | --- |
| `DATABASE_URL` | Backend | SQLAlchemy connection string pointed at the Supabase-managed Postgres database for the selected station role. |
| `SUPABASE_URL` | Backend, Frontend | Base URL for your Supabase project. Used by the frontend auth client and by backend management scripts. |
| `SUPABASE_ANON_KEY` | Frontend | Public Supabase key for client-side auth bootstrap and realtime subscriptions. |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend, Agents | Service-role key used by the backend and automation agents to apply migrations, run RLS bypass tasks, and manage Supabase auth webhooks. |
| `POSTGRES_STATION_ROLE` | All services | Role identifier (`ops`, `intel`, `logistics`) used to bind ChatKit channels to the correct AgentKit playbooks. |
| `POSTGRES_POOL_SIZE` | Backend | Optional override for multi-station connection pooling. |
| `CHATKIT_API_KEY` | Backend, Agents | API token for ChatKit orchestration. |
| `CHATKIT_ORG_ID` | Backend, Agents | Organization identifier required to join shared channels. |
| `AGENTKIT_CLIENT_ID` / `AGENTKIT_CLIENT_SECRET` | Agents | OAuth credentials for AgentKit workflow execution. |
| `STATION_CALLSIGN` | Frontend, Agents | Friendly identifier rendered in the UI header and propagated to telemetry events. |
| `TELEMETRY_BROADCAST_URL` | Agents | Optional WebSocket endpoint for streaming telemetry into ChatKit threads. |

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

The container helper now supports a Terraform-free flow: it first checks the forwarded config (`--config` or
`VTOC_CONFIG_JSON`) for a `configBundle` override, then falls back to [`scripts/defaults/config_bundle.local.json`](../scripts/defaults/config_bundle.local.json)
when Terraform outputs are unavailable. Copy that file, replace the placeholder secrets, and pass it through the setup CLI to
boot the stack without Terraform — the override takes precedence even when you opt into `--build-local` builds.

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

Make sure Supabase is reachable and that the generated `DATABASE_URL` references the correct hostname. For multi-station
setups using Supabase, verify that each schema (`ops`, `intel`, `logistics`) exists and that row-level security policies permit
your service-role key. When running against the optional local Postgres fallback, confirm the generated `_ops`, `_intel`,
`_logistics` databases are present.

## Next steps

- Review [`docs/TELEMETRY_CONNECTORS.md`](TELEMETRY_CONNECTORS.md) for connector-specific options.
- Plan your deployment strategy with [`docs/DEPLOYMENT.md`](DEPLOYMENT.md).
- Track platform changes in [`docs/CHANGELOG.md`](CHANGELOG.md).
