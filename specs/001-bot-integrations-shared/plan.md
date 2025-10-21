# Implementation Plan

## Phase 1 – Discovery & Alignment
- Interview ChatKit Server, AgentKit, and MCP owners to confirm supported command surfaces and authentication methods.
- Review `services` Dockerfiles and Fly deployment manifests to catalog reusable build steps.
- Audit existing OTEL exporters and logging utilities to ensure compatibility with long-running bot processes.

## Phase 2 – Shared Runtime Package
- Scaffold a `packages/bot-shared` TypeScript workspace module with lint/test configuration matching `frontend` tooling.
- Implement typed clients for ChatKit (REST + WebSocket), AgentKit (mission orchestration), Supabase (telemetry persistence), and MCP (command execution).
- Add configuration loader that validates environment variables against `scripts/inputs.schema.json` and exposes structured config objects.

## Phase 3 – Deployment & Configuration Assets
- Publish baseline Dockerfile extending `services/agentkit` runtime with shared dependencies and a lightweight supervisor.
- Extend `docker-compose.yml` with templated services for Telegram, Slack, and Discord bots referencing the shared image.
- Generate Fly.io app manifests and secrets guidance, ensuring secrets align with Doppler naming conventions.

## Phase 4 – Observability & Quality Gates
- Wire OTEL instrumentation, health endpoints (`/healthz`), and structured logging with correlation IDs.
- Add unit/integration tests that mock downstream services and validate retry/backoff behaviors.
- Document runbooks and sample dashboards in `docs/` for SRE handoff.

## Phase 5 – Rollout & Adoption
- Publish migration guide for platform-specific teams describing how to consume the shared package.
- Schedule joint review with security and operations to validate secrets management and monitoring coverage.
- Tag v1.0.0 of the shared package and coordinate releases with Telegram/Slack/Discord feature teams.
