# vTOC Architecture Overview

The vTOC platform combines a map-centric operations UI, a FastAPI backend, ChatKit collaboration channels, and AgentKit
playbooks orchestrating telemetry workflows. Stations are isolated by role yet share a Supabase-managed Postgres instance and a
ChatKit organization. This document describes the high-level architecture and the data flows that connect these components.

## System architecture

```
┌───────────────────────────────┐      ┌────────────────────────────┐
│   ChatKit Organization        │◄────►│   FastAPI Backend          │
│ - Shared channels per station │ Web  │ - REST/WS APIs             │
│ - Threaded ops logs           │hooks │ - ChatKit webhook handler  │
└─────────────┬─────────────────┘      │ - AgentKit dispatcher      │
              │                        └────────────┬───────────────┘
      Station messages                            │
              │                                   │ SQLAlchemy
┌─────────────▼──────────────┐           ┌────────▼──────────────┐
│   AgentKit Control Plane   │  Jobs     │   Supabase Postgres   │
│ - Role aware playbooks     ├──────────►│ - station_<role> DBs  │
│ - Telemetry connector shim │           │ - RLS + Auth context  │
└─────────────┬──────────────┘           └────────▲──────────────┘
              │                            │      │
      Task invocations                      │      │
              │                     ┌───────┴┐  ┌──┴────────┐
┌─────────────▼───────────┐        │ Backend │  │ Telemetry │
│ Frontend (Vite/React)   │        │  API    │  │  Scraper  │
│ - Mission map overlays   │ REST   │ Routers │  │ + Agents  │
│ - Chat console sidebar  ◄────────┴─────────┘  └───────────┘
│ - Station dashboards     │         ▲  ▲
└──────────────────────────┘         │  │
                                     │  │
                          ┌──────────┘  └───────────┐
                          │ External telemetry feeds │
                          └──────────────────────────┘
```

### Component summary

- **Frontend** — Vite + React application consuming backend APIs. Displays station status, mission overlays, and a ChatKit-driven
  mission console. Reads `STATION_CALLSIGN` and `POSTGRES_STATION_ROLE` from `.env.station`.
- **Backend** — FastAPI service exposing REST endpoints, ChatKit webhook listeners, and telemetry ingestion APIs. It maps channel
  events to AgentKit playbooks based on the station role and persists results to Supabase-hosted Postgres schemas.
- **Supabase Postgres** — Managed Postgres instance with per-role schemas (`ops`, `intel`, `logistics`). Supabase enforces
  row-level security policies aligned with station metadata and exposes realtime feeds for the frontend.
- **ChatKit Organization** — Shared chat fabric for operators and automated agents. Each station owns a default channel named
  after `STATION_CALLSIGN`. Channels contain threads for missions and telemetry alerts.
- **AgentKit** — Workflow runner that executes playbooks. Playbooks call telemetry connectors and use the backend APIs to log
  mission updates. Authentication uses `AGENTKIT_CLIENT_ID` / `AGENTKIT_CLIENT_SECRET`.
- **Telemetry connectors** — AgentKit tasks and scraper modules that ingest from ADS-B, AIS, APRS, etc. The connectors share the
  same configuration schema so they can be triggered manually or through ChatKit commands.

## Station roles

Stations isolate operator concerns:

| Role | Primary responsibilities | Default playbooks |
| --- | --- | --- |
| Operations (`ops`) | Mission coordination, asset deployment, chat command hub. | `op_order_frag`, `op_airtrack_merge`. |
| Intelligence (`intel`) | Sensor fusion, data enrichment, report generation. | `intel_sigint_rollup`, `intel_rfi_summary`. |
| Logistics (`logistics`) | Supply tracking, requisitions, status boards. | `log_restock_check`, `log_mission_loadout`. |

Playbook identifiers are defined under `agents/config/agentkit.yml`. The backend exposes them via `/api/v1/stations/<id>/playbooks`.

## Data flows

### Operator coordination

1. Operator sends a message in the station ChatKit channel.
2. ChatKit forwards the event to `/api/v1/chatkit/webhook`.
3. Backend validates the signature, resolves the station role, and queues an AgentKit job.
4. AgentKit executes the playbook, optionally invoking telemetry connectors.
5. Results are stored in Supabase Postgres and posted back to ChatKit. Frontend receives updates through the standard REST
   polling cycle.

#### Agent action audit context

- AgentKit invocations that flow through `/api/v1/agent-actions/execute` may carry optional ChatKit hints in the payload.
  Supply `channel_slug` and `initiator_id` either at the top level of the request body or inside the `metadata` object to
  persist the originating chat context alongside the audit record.
- ChatKit requests should include `X-ChatKit-Channel` (or `X-ChatKit-Thread`) and `X-ChatKit-User`/`X-ChatKit-Initiator`
  headers. The backend uses them as fallbacks when the JSON payload omits explicit context.
- Webhook callbacks can mirror the same `channel_slug` and `initiator_id` fields in their JSON body. The backend keeps the
  audit log up to date when the action completes, ensuring Supabase rows contain both execution status and chat metadata.

### Telemetry ingestion

1. Telemetry connector (standalone agent or AgentKit task) fetches external data.
2. Connector posts normalized payloads to `/api/v1/telemetry/events`.
3. Backend writes events to the station-specific Supabase schema and publishes notifications to ChatKit threads.
4. Frontend refreshes map overlays and mission intel panels.

### Station provisioning

1. Operator runs `make setup-local` or `make setup-container`.
2. Setup script reads `scripts/inputs.schema.json`, requests ChatKit/AgentKit credentials, and generates `.env.local` and
   `.env.station`.
3. When `--apply` is used, the script also bootstraps databases (`station_<role>`), registers roles in Postgres, and seeds
   default ChatKit channels.
4. Generated artefacts are referenced by Compose services and by `make compose-up`/`make compose-down` workflows.

## Security considerations

- **Secrets management** — Setup script writes environment files with restricted permissions. Rotate ChatKit/AgentKit credentials
  and Supabase keys regularly and supply them via your preferred secret store in production.
- **Webhook signing** — ChatKit webhook handler expects the `X-ChatKit-Signature` header. Configure the secret in
  `CHATKIT_WEBHOOK_SECRET` (optional override).
- **Database isolation** — Supabase schemas enforce row-level security per station. See
  [`docs/DEPLOYMENT.md`](DEPLOYMENT.md#multi-station-postgres-provisioning-with-supabase) for provisioning guidance.
- **Network segmentation** — Traefik routes external traffic while AgentKit and telemetry connectors run on internal networks.

## Related documentation

- [`docs/DIAGRAMS.md`](DIAGRAMS.md) — visual diagrams describing the same flows.
- [`docs/TELEMETRY_CONNECTORS.md`](TELEMETRY_CONNECTORS.md) — connector catalog with AgentKit notes.
- [`docs/CHANGELOG.md`](CHANGELOG.md) — migration guidance for ChatKit/AgentKit rollout.
