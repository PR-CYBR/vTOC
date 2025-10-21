# Tasks

_Feature: `bot-integrations`_

## 1. Cross-cutting discovery and infrastructure
- [ ] Audit ChatKit, AgentKit, and MCP interfaces required across bots.
- [ ] Define a shared bot service package with reusable clients, logging, and error handling.
- [ ] Extend configuration templates (.env files, inputs schema) for bot secrets and identifiers.
- [ ] Document deployment topology and secret management for the new services.
- [ ] Add shared health checks, structured logging, and observability hooks.

## 2. Telegram management bot
- [ ] Finalise the operator command surface and authorization guardrails.
- [ ] Implement Telegram transport handlers wired to shared helpers.
- [ ] Build command orchestration that returns structured responses to Telegram threads.
- [ ] Add deployment manifests and operator documentation for provisioning webhooks.
- [ ] Create automated tests covering command execution and error handling.

## 3. Slack monitoring bot
- [ ] Gather Slack credentials, scopes, and channel IDs for #vtoc.
- [ ] Implement Events API listeners and slash command endpoints on the shared framework.
- [ ] Mirror channel activity into ChatKit and AgentKit telemetry pipelines.
- [ ] Handle threading, deduplication, and Slack rate limiting resilience.
- [ ] Produce deployment artefacts and installation guides for the Slack app.

## 4. Discord operations bot
- [ ] Define Discord interaction modes, intents, and permissions for mission management.
- [ ] Implement Discord service handlers that execute ChatKit/AgentKit queries.
- [ ] Support pagination, ephemeral responses, and consistent error surfacing.
- [ ] Address reconnect, backoff, and secrets rotation scenarios unique to Discord.
- [ ] Ship deployment configuration and runbooks for registration and monitoring.

## 5. Documentation, QA, and rollout
- [ ] Update architecture diagrams to include multi-bot services.
- [ ] Extend contributor and operator docs with per-bot setup expectations.
- [ ] Add automated verification across shared utilities and platform-specific handlers.
- [ ] Produce end-to-end validation playbooks for local Compose and staging.
- [ ] Coordinate staged rollout with secrets provisioning, feature flags, and success metrics.
