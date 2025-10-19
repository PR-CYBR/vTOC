# Task Breakdown

## Command Manifest
- [ ] Draft slash command definitions and permissions.
- [ ] Register commands in staging guild and validate with stakeholders.

## Gateway Implementation
- [ ] Implement Discord.js gateway client with reconnect/backoff logic.
- [ ] Add health checks and metrics for connection state.

## Command Handlers
- [ ] Wire mission, playbook, diagnostics, and alerts handlers to shared clients.
- [ ] Support pagination, ephemeral responses, and follow-up messages for long operations.

## Resilience & Compliance
- [ ] Handle rate limit headers and implement circuit breaker for repeated failures.
- [ ] Record audit logs for command invocations in Supabase.
- [ ] Validate redaction requirements for sensitive mission data.

## Deployment & Rollout
- [ ] Produce Docker Compose and Fly.io manifests with secrets guidance.
- [ ] Document guild onboarding and invite process.
- [ ] Run staging rehearsal and collect approvals prior to production launch.
