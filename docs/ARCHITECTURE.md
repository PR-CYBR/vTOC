# vTOC Architecture Overview

The vTOC (Virtual Tactical Operations Center) stack is a lightweight telemetry portal that now embeds the ChatKit Co-Pilot to orchestrate AgentKit automations. The system is composed of three primary tiers—frontend, backend, and database—with supporting workflows and CI checks.

## High-Level Topology

```
┌──────────────────────────────────────────────────────────────────┐
│                              Browser                              │
│  React + Vite SPA                                                 │
│  ├─ React Query data fetching                                     │
│  ├─ React Router layout shell                                     │
│  └─ ChatKit Web Component (Co-Pilot)                              │
└───────────────▲──────────────────────────────────────────────────┘
                │ GraphQL/REST over HTTPS
┌───────────────┴──────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
│  ├─ Telemetry router (`/api/v1/telemetry/...`)                   │
│  ├─ Agent Actions router (`/api/v1/agent-actions/...`)           │
│  │    ├─ Tool metadata proxy                                     │
│  │    ├─ Action execution proxy                                  │
│  │    └─ ChatKit webhook handler                                 │
│  └─ Settings & AgentKit client abstraction                       │
└───────────────▲──────────────────────────────────────────────────┘
                │ SQLAlchemy ORM
┌───────────────┴──────────────────────────────────────────────────┐
│                        PostgreSQL Database                       │
│  ├─ `telemetry_sources`                                          │
│  ├─ `telemetry_events`                                          │
│  └─ `agent_action_audits` (new)                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

- **Framework**: React 18 + Vite.
- **State/Data**: `@tanstack/react-query` provides caching for telemetry feeds and ChatKit action audits.
- **Routing**: `react-router-dom` creates a persistent layout that keeps the ChatKit widget mounted while the user navigates between future routes.
- **ChatKit Integration**: The `ChatKitWidget` component loads the ChatKit web component, wires environment-based configuration (API key, AgentKit org, telemetry channel), and exposes current telemetry context so the assistant can reason about the map view.
- **Services**:
  - `services/api.ts` for telemetry REST calls.
  - `services/agentActions.ts` for AgentKit/ChatKit fulfilment with optimistic React Query mutations.
- **Testing**: Vitest unit tests cover the widget behaviours and React Query services, while Playwright runs a smoke E2E scenario that asserts the assistant renders and toggles correctly via the router shell.

### Required Frontend Environment Variables

| Variable | Purpose |
| --- | --- |
| `VITE_CHATKIT_WIDGET_URL` | Optional CDN path for loading the ChatKit web component script. |
| `VITE_CHATKIT_API_KEY` | Public API key issued by ChatKit for the workspace. |
| `VITE_CHATKIT_TELEMETRY_CHANNEL` | Topic identifier forwarded to the widget to scope events. |
| `VITE_AGENTKIT_ORG_ID` | AgentKit organisation id passed to ChatKit and backend proxies. |
| `VITE_AGENTKIT_DEFAULT_STATION_CONTEXT` | Default station/sector context shown to the assistant. |
| `VITE_AGENTKIT_API_BASE_PATH` | Base path for the backend Agent Actions API (defaults to `/api/v1/agent-actions`). |

## Backend Architecture

- **Framework**: FastAPI with SQLAlchemy ORM and Alembic migrations.
- **Routers**:
  - **Telemetry** – CRUD endpoints for sources and events, powering the intel feed and map markers.
  - **Agent Actions** – New router that
    1. proxies AgentKit tool metadata (`GET /tools`),
    2. queues AgentKit executions on behalf of ChatKit (`POST /execute`),
    3. ingests ChatKit webhooks with HMAC validation (`POST /webhook`), and
    4. exposes audit records (`GET /audits`).
- **Services**: `services/agentkit.py` encapsulates HTTP calls to AgentKit with consistent error handling and credential validation.
- **Data Model**: `AgentActionAudit` captures action lifecycle status, request payloads, and responses for observability and troubleshooting.
- **Configuration**: `config.Settings` loads AgentKit credentials, webhook secrets, and optional tool allow-lists from environment variables. The cache can be reset during tests.

### Required Backend Environment Variables

| Variable | Purpose |
| --- | --- |
| `AGENTKIT_API_BASE_URL` | Base URL for AgentKit API calls. |
| `AGENTKIT_API_KEY` | Bearer token used to authorise AgentKit requests. |
| `AGENTKIT_ORG_ID` | Organisation identifier applied to AgentKit endpoints. |
| `AGENTKIT_TIMEOUT_SECONDS` | Optional HTTP timeout (default 30s). |
| `CHATKIT_WEBHOOK_SECRET` | Shared HMAC secret for verifying ChatKit webhook signatures. |
| `CHATKIT_ALLOWED_TOOLS` | Optional comma-separated list restricting available AgentKit tools. |

## Data Persistence

Alembic migration `20240210_0002_agent_actions` introduces the `agent_action_audits` table. Each record tracks status transitions and metadata for AgentKit interactions. Telemetry tables remain unchanged from the initial migration.

## Operational Runbook for ChatKit Co-Pilot

1. **Provision credentials** – Obtain the ChatKit public API key and AgentKit API key/org id. Populate the frontend `.env` (or `.env.local`) and backend environment accordingly.
2. **Configure webhook** – Point ChatKit's webhook URL to `/api/v1/agent-actions/webhook` and use the same `CHATKIT_WEBHOOK_SECRET` in both ChatKit and backend configuration.
3. **Deploy migrations** – Run `alembic upgrade head` so the audit table exists before enabling the assistant.
4. **Smoke test** – Hit `/api/v1/agent-actions/audits` to confirm the backend responds, then trigger a sample action from ChatKit and verify a new audit row is written.
5. **Monitoring** – Use the audit log to observe running/failed states. CI executes unit tests plus Playwright smoke coverage to ensure the widget mounts correctly.

## Continuous Integration Enhancements

The CI workflow installs Playwright browsers, runs Vitest unit tests, executes Playwright smoke tests against a Vite preview build, exercises FastAPI unit tests (including webhook signature handling), and curls the new `/api/v1/agent-actions/audits` endpoint during the container smoke stage.

Together, these layers ensure the ChatKit Co-Pilot remains stable, observable, and fully integrated into the vTOC operational dashboard.
