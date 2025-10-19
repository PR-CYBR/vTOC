# Bot Rollout Checklist Contract

## Purpose
Define the minimum artifacts and validations required before promoting Telegram, Slack, or Discord bots through environments.

## Environments & Gates
- **Local**: Developers must run shared + platform-specific test suites and validate health endpoints via Compose.
- **Staging**: Deploy shared runtime image plus bot services to Fly.io staging apps; execute integration playbooks and confirm monitoring dashboards.
- **Production**: Requires change management approval, secrets validation, and successful staging sign-off within previous 24 hours.

## Required Artifacts
- Updated spec and plan documents reflecting scope and deployment decisions.
- Operator runbooks, incident response guides, and contact matrices stored in `docs/operations/`.
- QA reports summarizing test coverage, pass/fail status, and outstanding issues.

## Validation Steps
- Verify secrets in Doppler/Fly match expected naming convention and access policies.
- Confirm OTEL traces, logs, and Supabase telemetry entries appear for smoke test commands.
- Run rollback drill documentation to ensure teams can disable bots quickly if needed.

## Sign-off
- Product lead, operations lead, and security reviewer must sign the rollout checklist.
- Post-launch review scheduled within two weeks to capture learnings and update documentation.
