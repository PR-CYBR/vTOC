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
  - `/api/v1/stations/{station_slug}/timeline` merges recent telemetry events with AgentKit audits so operators can review a
    unified activity feed per station.
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

### Timeline summary playbook

- **Identifier:** `timeline_summary`
- **Entrypoint:** `agents.playbooks.timeline_summary:TimelineSummaryPlaybook`
- **Purpose:** Fetch the latest `/api/v1/stations/<slug>/timeline` payload with station-scoped credentials and render a Markdown
  digest suitable for posting back into ChatKit threads.
- **Environment:** The AgentKit runner must provide `BACKEND_BASE_URL`, `STATION_API_TOKEN`, and `POSTGRES_STATION_ROLE`
  (or `STATION_SLUG`) so the playbook can authenticate and select the correct station context.
- **Invocation:** `agentkit run timeline_summary --limit 5` will return a compact summary and attach the raw timeline payload in
  the execution metadata. This command can be wired to ChatKit slash commands or scheduled automations.

## Data flows

### ChatKit & AgentKit Workflow

The ChatKit and AgentKit integration enables operators to coordinate missions and execute automated workflows through chat commands:

**Architecture:**
1. **ChatKit Channels:** Each station has a dedicated channel (e.g., `#ops-toc-s1`) where operators collaborate
2. **Webhook Integration:** ChatKit sends events to `/api/v1/chatkit/webhook` when messages are posted
3. **Backend Processing:** FastAPI validates webhook signatures and routes commands to appropriate handlers
4. **AgentKit Playbooks:** Backend triggers AgentKit playbooks based on message content and station role
5. **Result Publishing:** Playbook outputs are posted back to ChatKit and stored in Supabase

**Command Flow:**
```
Operator types: @agent check status
    ↓
ChatKit webhook → Backend validates → Resolves station role
    ↓
Backend triggers: AgentKit playbook "timeline_summary"
    ↓
Playbook queries: /api/v1/stations/{slug}/timeline
    ↓
Results posted: Back to ChatKit thread + stored in Postgres
    ↓
Frontend updates: Map overlays and mission console
```

**Key Components:**
- **ChatKit Organization:** Shared workspace for all stations and operators
- **Station Channels:** Role-specific channels (`ops`, `intel`, `logistics`)
- **AgentKit Playbooks:** Automated workflows defined in `agents/config/agentkit.yml`
- **Webhook Handler:** FastAPI endpoint processing ChatKit events
- **Audit Trail:** All AgentKit invocations logged in Supabase with chat context

**Supported Operations:**
- Mission planning and coordination
- Telemetry data queries and analysis
- Station status checks and timeline summaries
- POI/IMEI watchlist management
- Report generation and intelligence briefings

See [`docs/POI-IMEI.md`](POI-IMEI.md) for POI tracking workflows and [`docs/DEPLOYMENT.md`](DEPLOYMENT.md#chatkit-configuration-steps) for ChatKit setup.

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

### POI and IMEI tracking

The POI (Person of Interest) and IMEI tracking system provides automatic alerting when known device identifiers appear in telemetry:

1. Operators create POI records via `/api/v1/poi` with associated identifiers (IMEI, MAC, callsign, phone).
2. IMEIs are added to watchlists (blacklist or whitelist) via `/api/v1/imei-watchlist`.
3. When telemetry contains an IMEI field:
   - Backend checks IMEI against the watchlist during event creation.
   - **Blacklist hits** generate `imei_blacklist_hit` events (high-severity alerts).
   - **Whitelist sightings** generate `imei_whitelist_seen` events (tracking/informational).
   - Event payload is enriched with POI context (name, risk level, category).
4. Timeline queries return POI alert entries (`StationTimelinePoiAlertEntry`) alongside regular telemetry.
5. ChatKit webhook posts alert messages to station channels for blacklist hits.
6. Frontend displays alerts with visual indicators (red for blacklist, green for whitelist) and filtering options.

The POI/IMEI pipeline integrates seamlessly with existing telemetry ingestion, requiring only that telemetry payloads include an `imei` or `IMEI` field. See [`docs/POI-IMEI.md`](POI-IMEI.md) for operator workflows and detailed usage.

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
- **POI/IMEI data** — POI records and watchlist entries contain sensitive intelligence. Access is restricted to authorized operators, and all operations are audited.

## Related documentation

- [`docs/DIAGRAMS.md`](DIAGRAMS.md) — visual diagrams describing the same flows.
- [`docs/POI-IMEI.md`](POI-IMEI.md) — POI tracking and IMEI alerting operator guide.
- [`docs/TELEMETRY_CONNECTORS.md`](TELEMETRY_CONNECTORS.md) — connector catalog with AgentKit notes.
- [`docs/CHANGELOG.md`](CHANGELOG.md) — migration guidance for ChatKit/AgentKit rollout.
