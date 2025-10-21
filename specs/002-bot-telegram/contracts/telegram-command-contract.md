# Telegram Command Contract

## Purpose
Ensure Telegram operator commands map cleanly to shared runtime handlers while respecting platform limits and security posture.

## Command Surface
- `/status <mission>` – returns mission summary, current phase, and active incidents.
- `/playbook <name> [--dry-run]` – triggers AgentKit playbook and returns execution tracking link.
- `/diagnostics <system>` – runs MCP diagnostic commands and reports outcome with remediation hints.
- `/help` – lists available commands and contact channels.

## Validation Rules
- All commands require operator ID in the allow list stored in Supabase.
- Rate limiting: default 10 commands per minute per operator; overflow returns cooldown message.
- `/playbook` requires confirmation prompt for destructive actions (two-step inline button flow).

## Response Expectations
- MarkdownV2 formatted messages with fallback plain text for legacy clients.
- Attachments limited to 1MB; larger payloads link to Supabase-generated signed URLs.
- Include correlation ID in footer for referencing logs and OTEL traces.

## Error Handling
- Known errors (validation, auth) return descriptive message and recommended next steps.
- Unknown errors trigger escalation to on-call via AgentKit and return generic failure with correlation ID.
