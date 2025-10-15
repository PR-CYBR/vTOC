# vTOC Implementation Summary

## Overview

This iteration wires the ChatKit Co-Pilot into the existing telemetry dashboard. The React frontend now exposes a routed layout with a persistent assistant panel, while the FastAPI backend proxies AgentKit operations, logs action lifecycle data, and secures ChatKit webhooks.

## Frontend Enhancements

- Introduced a router shell (`react-router-dom`) so the telemetry map renders via nested routes and the assistant remains mounted.
- Added `ChatKitWidget` to encapsulate loading the ChatKit web component, bind telemetry context, and expose environment-driven configuration.
- Implemented `services/agentActions.ts` providing React Query queries/mutations for AgentKit tools, audits, and optimistic execution flows.
- Expanded styling to support a dedicated assistant container and interaction controls.
- Added Vitest unit tests for the widget plus Playwright smoke coverage that boots a Vite preview build and toggles the assistant UI.

## Backend Enhancements

- Created `config.Settings` to manage AgentKit credentials, timeouts, and webhook secrets.
- Added an `AgentKitClient` service for consistent HTTP interactions (tool listing, action execution, action lookup) with error surfacing.
- Introduced the `/api/v1/agent-actions` router exposing:
  - `GET /tools` – filtered tool metadata from AgentKit.
  - `POST /execute` – executes AgentKit tools and records audit rows.
  - `GET /audits` – surfaces recent action audit entries.
  - `POST /webhook` – validates ChatKit HMAC signatures and updates audit records.
- Added the `agent_action_audits` SQLAlchemy model and Alembic migration `20240210_0002_agent_actions`.
- Wrote pytest coverage for the execution endpoint and webhook signature validation using an in-memory SQLite database and dependency overrides.

## Tooling & CI

- Updated requirements to include `httpx`, `pytest`, and `pytest-asyncio` for backend testing, plus `@playwright/test` on the frontend.
- Extended the GitHub Actions workflow to install Playwright browsers, run Playwright tests after the Vite build, and add a smoke assertion for the new `/api/v1/agent-actions/audits` endpoint.

## Configuration Summary

| Scope | Variable | Description |
| --- | --- | --- |
| Frontend | `VITE_CHATKIT_API_KEY` | Public ChatKit key required to render the assistant. |
| Frontend | `VITE_AGENTKIT_ORG_ID` | AgentKit org id shared with the backend and widget. |
| Frontend | `VITE_AGENTKIT_DEFAULT_STATION_CONTEXT` | Default mission/sector context passed to the assistant. |
| Backend | `AGENTKIT_API_BASE_URL` | AgentKit REST base URL. |
| Backend | `AGENTKIT_API_KEY` | AgentKit bearer token. |
| Backend | `CHATKIT_WEBHOOK_SECRET` | Secret used to verify incoming ChatKit webhooks. |

Populate these values locally using `scripts/setup_local.sh`, `.env.local`, or platform secrets before enabling the assistant in production.
