# Task Breakdown

## Command Catalog
- [ ] Document mission status, AgentKit playbook, and MCP diagnostic commands with sample responses.
- [ ] Define RBAC allow list and rate limit thresholds.

## Transport Implementation
- [ ] Implement webhook endpoint with signature verification and fallback polling worker.
- [ ] Configure Fly.io deployment with secrets and TLS certificates.
- [ ] Provide local Compose service and tunneling instructions.

## Command Handlers
- [ ] Wire `/status`, `/playbook`, `/diagnostics`, and `/help` handlers to shared clients.
- [ ] Implement pagination helpers and MarkdownV2 formatting utilities.
- [ ] Add retries, error messaging, and escalation notifications.

## Testing & Observability
- [ ] Create integration tests using Telegram sandbox payloads.
- [ ] Instrument OTEL spans and structured logs for key command paths.
- [ ] Validate Supabase audit logging and rate limit enforcement.

## Documentation & Rollout
- [ ] Write operator onboarding guide and runbooks.
- [ ] Conduct staging dry-run and capture approvals.
- [ ] Schedule production rollout and monitor metrics.
