# Research Notes

## Platform Insights
- Telegram Bot API supports both long-polling (`getUpdates`) and webhook modes; Fly.io favors webhook due to stable URLs.
- Rate limits: 30 messages per second overall, 1 message per second per chat—handlers must throttle responses.
- MarkdownV2 formatting requires escaping special characters; build helper utilities to avoid runtime errors.

## Dependencies
- Shared runtime (`specs/001-bot-integrations-shared`) provides ChatKit/AgentKit/MCP clients and config validation.
- Supabase table for operator allow list—confirm schema and add migration if necessary.
- Notification channel for incident escalation (likely via existing PagerDuty integration triggered from AgentKit).

## Outstanding Questions
- Determine hosting region to minimize latency to Telegram data centers.
- Clarify if missions with classified data require redaction before returning results.
- Confirm how audit logs should be stored (Supabase vs centralized logging pipeline).
