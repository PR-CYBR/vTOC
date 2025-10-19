# Quickstart

1. Install workspace dependencies: `pnpm install`.
2. Create `.env.slack` with `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_APP_LEVEL_TOKEN`, and `MONITORED_CHANNELS`.
3. Start local dependencies: `docker compose up chatkit-server agentkit supabase`.
4. Launch the bot: `pnpm --filter bot-slack dev -- --env-file .env.slack`.
5. Use `pnpm --filter bot-slack run register-events --tunnel-url <https://...>` to configure event subscriptions during local testing.
6. Post messages in the target Slack channel and verify telemetry records appear in Supabase plus OTEL traces in the collector dashboard.
