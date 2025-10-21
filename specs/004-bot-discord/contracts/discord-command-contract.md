# Discord Command Contract

## Purpose
Describe expectations for Discord slash commands and interaction flows backed by the shared runtime.

## Commands
- `/mission [id]` – returns mission status summary and incident links; defaults to active mission if omitted.
- `/playbook name:<string> confirm:<boolean>` – invokes AgentKit playbook with optional confirmation step.
- `/diagnostics system:<string>` – triggers MCP diagnostics and returns structured output.
- `/alerts` – lists unresolved alerts with pagination controls.

## Interaction Rules
- Initial response must be sent within 3 seconds using `interaction.deferReply()` when processing requires more time.
- Sensitive data responses (`/playbook`, `/diagnostics`) default to ephemeral visibility.
- Pagination uses custom IDs that expire after 15 minutes to reduce stale interactions.

## Error Handling
- Validation failures return ephemeral error messages with corrective actions.
- Downstream outages respond with ephemeral message referencing incident channel and correlation ID.
- Gateway disconnects trigger auto-resume and send notification to operations Discord channel if resume fails after 3 attempts.

## Observability
- Emit OTEL spans with attributes `discord.command`, `discord.guild_id`, and `discord.user_id` (hashed for privacy).
- Log command invocations and outcomes to Supabase audit table.
- Track metrics for command success rate, latency percentiles, and reconnect counts.
