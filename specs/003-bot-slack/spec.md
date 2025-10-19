# Slack Monitoring Bot Spec

## Summary
Develop a Slack bot that listens to designated channels, mirrors relevant activity into vTOC telemetry pipelines, and surfaces key alerts to operators. The bot leverages the shared runtime while focusing on Slack Events API integration and message processing workflows.

## Goals
- Acquire necessary Slack app credentials, scopes, and event subscriptions for monitored channels.
- Implement Slack Events API listener and optional slash commands using shared runtime primitives.
- Process messages into structured telemetry, including deduplication and enrichment.
- Provide deployment assets and operations documentation for Slack app lifecycle management.

## Non-Goals
- Replace Slack workspace governance or provisioning processes.
- Implement cross-platform shared logic already handled in `001-bot-integrations-shared`.

## Scope & Deliverables
- Slack app manifest and scope definitions.
- Events API listener service with signature verification and retry handling.
- Message normalization pipeline that feeds Supabase telemetry tables and triggers ChatKit alerts when necessary.
- Slash commands (e.g., `/vtoc-status`) for on-demand summaries.
- Deployment templates for Docker Compose and Fly.io, plus runbooks for installation and monitoring.

## Architecture Overview
- **Events Intake**: Express endpoint `/slack/events` verifying signing secrets and responding within 3 seconds.
- **Processing Pipeline**: Shared runtime dispatches events to message processors that handle channel filters, deduplication, and summarization.
- **Telemetry Output**: Normalized events stored in Supabase; high-priority items forwarded to ChatKit notifications.
- **Commands**: Slash commands call ChatKit/AgentKit clients for real-time updates.
- **Deployment**: Fly.io app with autoscaling tuned for burst events; Compose service for local testing with ngrok.

## Milestones
1. Slack app manifest drafted and approved by workspace admins.
2. Events API listener implemented with verification tests.
3. Message processing pipeline connected to Supabase and ChatKit notifications.
4. Slash commands and telemetry dashboards validated in staging.

## Open Questions & Clarifications
All `[NEEDS CLARIFICATION]` items resolved while drafting. Pending topics (workspace admin approvals) are tracked in plan tasks.

## References
- Legacy task context: `docs/tasks/bot-integrations.md#3-slack-monitoring-bot`.
- Shared runtime spec: `specs/001-bot-integrations-shared/spec.md`.
