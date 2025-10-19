# Bot Integrations Shared Infrastructure Spec

## Summary
Deliver a reusable foundation for the Telegram, Slack, and Discord bots so they can call vTOC's ChatKit Server, AgentKit, Supabase, and MCP services with consistent deployment, configuration, and observability patterns. The shared layer centralizes authentication, telemetry, and runtime packaging before any platform-specific logic ships.

## Goals
- Catalogue shared ChatKit, AgentKit, MCP, and Supabase interfaces that each bot must consume.
- Publish a language runtime, dependency management, and packaging baseline that all bot services inherit.
- Define environment configuration, secrets management, and deployment topology reusable across containers, Docker Compose, and Fly.io.
- Ship cross-cutting health checks, logging, and metrics hooks compatible with existing observability pipelines.

## Non-Goals
- Implement any platform-specific transports or command handlers (covered by the Telegram, Slack, and Discord specs).
- Replace existing ChatKit or AgentKit service contracts—the work focuses on client reuse, not server refactors.

## Scope & Deliverables
- Shared client library that wraps ChatKit Server HTTP/WebSocket APIs, AgentKit workflows, and MCP commands with consistent error handling.
- Templates for Dockerfiles, Fly.io apps, Compose services, and Kubernetes manifests where applicable.
- Environment schema updates (`.env`, `scripts/inputs.schema.json`) including validation for bot credentials.
- Observability primitives (structured logs, OTEL exporters, health probes) rolled into the shared runtime.

## Architecture Overview
- **Runtime**: Node.js 20 with TypeScript service scaffolding aligned with existing frontend/backend packaging. Each bot runs as an independent process but imports the shared package.
- **Service Clients**: Shared module exposes typed clients for ChatKit Server (gRPC/WebSocket bridges), AgentKit REST flows, Supabase data fetches, and MCP command invocations.
- **Configuration**: `.env` templates enumerate tokens (`TELEGRAM_BOT_TOKEN`, `SLACK_BOT_TOKEN`, `DISCORD_BOT_TOKEN`), signing secrets, and channel IDs. Secrets flow through Doppler/Fly secrets for production and Compose overrides for local.
- **Deployment**: Docker base image extends existing `services/bots` image with install scripts. Compose adds services under `bots-*`, while Fly gets dedicated apps using the shared buildpack.
- **Observability**: Shared logger pushes JSON logs to stdout with structured fields; OTEL traces/reporting integrate with existing collector sidecars defined in `infrastructure/otel`.

## Milestones
1. Discovery and API inventory completed with documentation.
2. Shared runtime package published with linting/tests.
3. Deployment assets (Dockerfile, Compose, Fly) templated and validated locally.
4. Observability hooks wired and documented with sample dashboards.

## Open Questions & Clarifications
All `[NEEDS CLARIFICATION]` markers from the legacy doc were addressed during drafting—no outstanding blockers remain. Future platform questions should be tracked within the platform-specific specs.

## References
- Legacy backlog context: `docs/tasks/bot-integrations.md#1-cross-cutting-discovery-and-infrastructure` (retained for historical notes).
- Related services: `backend/chatkit-server`, `services/agentkit`, `infrastructure/otel`.
