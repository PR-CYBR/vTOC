# Telegram Management Bot Spec

## Summary
Build a Telegram bot that enables vTOC operators to query mission status, trigger AgentKit playbooks, and run MCP diagnostics using the shared bot runtime. The bot must enforce authorization controls and deliver reliable responses tailored to Telegram chats.

## Goals
- Finalize operator command catalog covering mission insights, AgentKit automation, and MCP tooling.
- Implement Telegram transport (webhook or long-polling) integrated with the shared runtime package.
- Deliver robust command handlers that orchestrate ChatKit, AgentKit, and MCP workflows.
- Provide deployment manifests and operator documentation for provisioning Telegram bots.

## Non-Goals
- Redesign Telegram's UX or replace platform-native authentication flows.
- Implement shared infrastructure primitives already defined in `001-bot-integrations-shared`.

## Scope & Deliverables
- Command definitions with role-based access control and rate limiting.
- Transport adapter supporting webhook mode (preferred for Fly.io) with fallback polling for local development.
- Command handler modules that fan out to ChatKit/AgentKit/MCP clients and format Telegram-safe responses.
- Deployment artifacts: Dockerfile stage referencing shared runtime, Compose service, Fly app config, and runbook updates.
- Test harness simulating Telegram updates to validate command flows and error recovery.

## Architecture Overview
- **Entry Point**: Shared runtime bootstraps Express server exposing `/telegram/webhook` and `/healthz` endpoints.
- **Authentication**: Validate incoming updates with Telegram secret token; enforce allow list of operator IDs stored in Supabase.
- **Command Routing**: `BotApp` registers commands mapped to handler modules; handlers use shared clients for ChatKit (mission status), AgentKit (playbook triggers), and MCP (diagnostics).
- **Response Formatting**: Use MarkdownV2 formatting, chunk large payloads, and provide inline buttons for pagination.
- **Deployment**: Fly.io app with webhook URL; local Compose uses polling worker with ngrok-style tunneling instructions captured in quickstart.

## Milestones
1. Command catalog documented and reviewed with operators.
2. Transport adapter implemented with integration tests against Telegram sandbox.
3. Command handlers wired to shared clients with unit tests and stub data.
4. Deployment assets validated in staging; runbooks published.

## Open Questions & Clarifications
No outstanding `[NEEDS CLARIFICATION]` markers remain. Open items (like final webhook hosting region) will be tracked in plan tasks.

## References
- Legacy task context: `docs/tasks/bot-integrations.md#2-telegram-management-bot`.
- Shared runtime spec: `specs/001-bot-integrations-shared/spec.md`.
