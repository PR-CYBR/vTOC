# Task Breakdown

## Discovery
- [ ] Document ChatKit, AgentKit, MCP, and Supabase endpoints required by all bots.
- [ ] Collect authentication and secret rotation requirements from security engineering.

## Shared Runtime Package
- [ ] Create `packages/bot-shared` workspace with lint/test setup.
- [ ] Implement ChatKit/AgentKit/Supabase/MCP client wrappers with retry/backoff helpers.
- [ ] Provide configuration loader enforcing `.env` schema and producing typed config objects.

## Deployment Assets
- [ ] Author shared Dockerfile and Compose service templates.
- [ ] Produce Fly.io app manifests and secrets documentation.
- [ ] Update `.env.example` and `scripts/inputs.schema.json` with bot credentials.

## Observability & QA
- [ ] Integrate OTEL tracing, structured logging, and `/healthz` endpoint.
- [ ] Add integration tests mocking downstream services.
- [ ] Create sample dashboards/runbooks for SRE and feature teams.

## Adoption
- [ ] Publish migration guide for Telegram/Slack/Discord bot owners.
- [ ] Schedule enablement session covering shared package usage.
