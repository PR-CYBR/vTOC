# Quickstart

1. Install dependencies with `pnpm install` to make the shared TypeScript workspace available.
2. Run `pnpm --filter bot-shared test` to execute baseline unit tests for the shared clients.
3. Start local infrastructure: `docker compose up supabase chatkit-server agentkit` to provide downstream services.
4. Launch an example bot using the shared runtime: `pnpm --filter bot-sample dev` (sample entrypoint loads `.env.local`).
5. Verify health endpoints at `http://localhost:8080/healthz` and confirm OTEL traces appear in the local collector dashboard.
6. Update `.env.example` and `scripts/inputs.schema.json` with bot credential placeholders, then re-run `pnpm lint` to validate schema synchronization.
