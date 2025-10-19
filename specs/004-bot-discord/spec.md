# Discord Operations Bot Spec

## Summary
Create a Discord bot that exposes mission management capabilities, real-time data retrieval, and operational workflows to Discord guild members. The bot builds atop the shared runtime and emphasizes Discord interaction models, rate limiting, and reconnect strategies.

## Goals
- Define slash commands and message components providing mission status, AgentKit orchestration, and MCP diagnostics.
- Implement Discord gateway and REST integrations with resilient reconnect/backoff behavior.
- Support real-time data retrieval with pagination, ephemeral responses, and consistent error surfacing.
- Deliver deployment assets and runbooks covering registration, invites, and monitoring.

## Non-Goals
- Replace Discord guild management policies or role assignment automation.
- Duplicate shared infrastructure addressed in `001-bot-integrations-shared`.

## Scope & Deliverables
- Discord application manifest (commands, intents, permissions).
- Gateway connection handling using Discord.js (or similar) with sharding support.
- Command handlers bridging ChatKit, AgentKit, and MCP services.
- Deployment configuration for Docker Compose and Fly.io, including secret rotation guidance.
- Observability instrumentation for reconnects, latency, and command success rates.

## Architecture Overview
- **Connection Layer**: Gateway client maintains websocket connection with exponential backoff; REST client handles slash command registration.
- **Command Framework**: Shared runtime hosts command registry; Discord-specific adapters map interactions to handlers.
- **Response Handling**: Use ephemeral responses for sensitive data, follow-up messages for long-running operations, and pagination for list outputs.
- **Deployment**: Compose service for local testing; Fly.io app with worker process handling gateway events and background tasks.
- **Observability**: OTEL spans annotate `discord.event_type`; metrics capture reconnect counts, latency, and command outcomes.

## Milestones
1. Command manifest drafted and reviewed with operations stakeholders.
2. Gateway connection and reconnect logic implemented with integration tests.
3. Command handlers wired to shared clients with pagination and ephemeral response support.
4. Deployment assets validated and runbooks published.

## Open Questions & Clarifications
No unresolved `[NEEDS CLARIFICATION]` markers remain. Outstanding details (like final shard counts) will be addressed in plan execution.

## References
- Legacy task context: `docs/tasks/bot-integrations.md#4-discord-operations-bot`.
- Shared runtime spec: `specs/001-bot-integrations-shared/spec.md`.
