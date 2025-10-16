# Multi-Platform Bot Integration Plan

This plan organizes the work required to introduce Telegram, Slack, and Discord bots that integrate with vTOC's ChatKit Server, AgentKit, and related services. Tasks are grouped to maximize reuse of shared bot infrastructure while respecting each platform's unique requirements.

## 1. Cross-cutting discovery and infrastructure
- [ ] Audit existing ChatKit/AgentKit/MCP interfaces to catalogue commands, authentication schemes, and payload formats required by all bots.
- [ ] Design a shared bot service package (language runtime, dependency management, logging, error handling) with reusable clients for ChatKit, AgentKit, Supabase, and MCP.
- [ ] Establish configuration standards: extend `.env` templates, `scripts/inputs.schema.json`, and documentation with bot tokens, signing secrets, and channel identifiers.
- [ ] Define deployment topology (Dockerfiles, Compose services, Fly.io configuration) and secret management approach for the new bot services.
- [ ] Implement health checks, structured logging, and observability hooks shared across all bots.

## 2. Telegram management bot
- [ ] Finalize operator command set (mission status, AgentKit playbooks, MCP queries) and authorization guardrails (allowed user IDs, rate limits).
- [ ] Implement Telegram bot transport (webhook or long-polling) wired to the shared client helpers.
- [ ] Build command handlers that orchestrate ChatKit/AgentKit/MCP calls and return structured responses back to Telegram threads.
- [ ] Add deployment manifests (Dockerfile/Compose service, Fly config) and document Telegram setup (bot token provisioning, webhook URL).
- [ ] Create unit/integration tests or mocks covering command execution paths and error handling.

## 3. Slack monitoring bot
- [ ] Gather required Slack app credentials, scopes, event subscriptions, and target channel IDs for the `#vtoc` text channel.
- [ ] Implement Slack Events API listener and optional slash command endpoints using the shared bot framework.
- [ ] Develop message processing logic that mirrors or summarizes channel activity into ChatKit/AgentKit telemetry pipelines.
- [ ] Handle message threading, deduplication, and resilience against Slack rate limits or transient failures.
- [ ] Provide deployment artifacts and operator documentation for Slack app installation, token management, and monitoring.

## 4. Discord operations bot
- [ ] Define Discord interaction model (slash commands, message components) and required intents/permissions for mission management.
- [ ] Implement Discord bot service leveraging the shared helpers to execute ChatKit/AgentKit queries and respond in-channel.
- [ ] Support real-time data retrieval, including pagination, ephemeral responses, and error surfacing consistent with Discord UX.
- [ ] Address Discord-specific concerns: rate limit handling, reconnect/backoff strategies, and secrets rotation.
- [ ] Package deployment configuration and provide runbooks for Discord bot registration, invite flows, and operational monitoring.

## 5. Documentation, QA, and rollout
- [ ] Update architecture and deployment diagrams to include the new bot services and their interaction points.
- [ ] Extend contributor and operator docs with setup steps, security expectations, and troubleshooting guides for each bot.
- [ ] Add automated verification (unit tests, contract tests, CI workflows) covering shared utilities and platform-specific handlers.
- [ ] Produce end-to-end validation playbooks for local docker-compose and staging environments.
- [ ] Coordinate staged rollout plan including secrets provisioning, feature flags, and success metrics.
