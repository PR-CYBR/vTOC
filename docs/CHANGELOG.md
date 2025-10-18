# vTOC ChatKit/AgentKit Transition Guide

This document highlights the key changes introduced with the ChatKit + AgentKit release and provides migration guidance for
existing operators. Cross-links point to updated documentation for deeper detail.

## Summary of changes

- Adopted ChatKit channels per station for collaborative mission logs.
- Integrated AgentKit playbooks for role-aware automation.
- Added station role aware Postgres provisioning (`vtoc_ops`, `vtoc_intel`, `vtoc_logistics`).
- Introduced new environment variables (`CHATKIT_API_KEY`, `CHATKIT_ORG_ID`, `AGENTKIT_CLIENT_ID`, `AGENTKIT_CLIENT_SECRET`,
  `POSTGRES_STATION_ROLE`, `STATION_CALLSIGN`, `TELEMETRY_BROADCAST_URL`).
- Updated setup scripts (`make setup-local`, `make setup-container`, `make setup-cloud`) to provision ChatKit resources.
- Revamped documentation: [`README.md`](../README.md), [`docs/QUICKSTART.md`](QUICKSTART.md),
  [`docs/ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](DEPLOYMENT.md), [`docs/TELEMETRY_CONNECTORS.md`](TELEMETRY_CONNECTORS.md).
- Introduced an automated discussion summary workflow that posts release notes to GitHub Discussions when `main` is updated (see [`Main discussion summary`](workflows/main-discussion-summary.md)).

## Migration steps

1. **Pull latest code** — ensure your repository is up to date with the ChatKit release.
2. **Regenerate environment files** — run `make setup-local` to create `.env.local` and `.env.station`. Provide the new ChatKit
   and AgentKit credentials when prompted.
3. **Provision databases** — create `vtoc_<role>` databases or migrate existing schemas. See
   [`docs/DEPLOYMENT.md`](DEPLOYMENT.md#multi-station-postgres) for SQL and Terraform examples.
4. **Run migrations** — execute `alembic upgrade head` for each station role to create the telemetry and chat tables.
5. **Configure ChatKit webhook** — point ChatKit to `/api/v1/chatkit/webhook` and set the signature secret to match your
   environment variables.
6. **Update AgentKit playbooks** — ensure `agents/config/agentkit.yml` contains entries for each station role. Document any custom
   connectors in [`docs/TELEMETRY_CONNECTORS.md`](TELEMETRY_CONNECTORS.md).
7. **Redeploy services** — use `make compose-up`, Docker Swarm, or Fly.io (`git checkout live && flyctl deploy`) to redeploy with
   the new images.
8. **Verify flows** — confirm ChatKit interactions trigger AgentKit runs and telemetry connectors post data to the correct
   station database.
9. **Review documentation automation** — provision the `CODEX_API_KEY` secret and `DOCS_DISCUSSION_CATEGORY_ID` variable so the
   discussion-summary workflow can publish updates after merges to `main`.

## Maintenance notes

- Rotate the `CODEX_API_KEY` credential at the same cadence as other automation secrets and update it in repository settings.
- Update `DOCS_DISCUSSION_CATEGORY_ID` when the deployment discussion category is reorganized or renamed in GitHub.
- Monitor the discussion-summary workflow for failures and re-run it via `workflow_dispatch` when deployment notes need to be
  regenerated.

## Known compatibility notes

- Existing `.env` files without the new variables will cause startup failures. Regenerate them using the setup script.
- Legacy missions without ChatKit thread IDs continue to render but will not receive retroactive chat logs.
- AgentKit playbooks require `station_role` matching the database suffix; update custom automations accordingly.

For questions or feedback file an issue and reference the relevant section in this guide. Thank you for operating vTOC!
