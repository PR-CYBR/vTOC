# Research Notes

## Existing Assets
- `backend/chatkit-server`: source of mission command APIs, existing telemetry hooks, and auth middleware patterns.
- `services/agentkit`: reference TypeScript service packaging, environment management, and gRPC bridges.
- `infrastructure/otel`: OTEL collector configuration and dashboards to replicate for bot observability.
- `scripts/inputs.schema.json`: authoritative schema for environment variables—needs bot-specific extensions.

## External References
- Telegram, Slack, and Discord API docs for authentication flows and rate limiting (shared constraints inform client abstractions).
- Fly.io multi-app deployment guides for shared Docker images and secret propagation.

## Open Findings
- Confirm whether ChatKit exposes WebSocket subscriptions required by Slack/Discord streaming scenarios.
- Determine if AgentKit mission orchestration supports impersonation contexts needed for bot-initiated runs.
- Validate Supabase throttling limits when aggregating telemetry from multiple bots through shared pipelines.

## Decisions to Record Later
- Final language/runtime selection (Node.js assumed; confirm with platform teams).
- Location of shared package within monorepo workspace structure.
- Choice of metrics exporter (OTLP HTTP vs gRPC) based on collector compatibility.
