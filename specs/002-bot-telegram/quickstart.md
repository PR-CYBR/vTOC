# Quickstart

1. Enable the shared runtime workspace: `pnpm install && pnpm --filter bot-shared build`.
2. Create `.env.telegram` with `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, and `OPERATOR_ALLOWLIST` entries.
3. Start dependencies: `docker compose up chatkit-server agentkit supabase`.
4. Run the bot locally in polling mode: `pnpm --filter bot-telegram dev -- --env-file .env.telegram`.
5. For webhook testing, expose local server via `ssh -R` or `cloudflared` and register the public URL with `pnpm --filter bot-telegram run register-webhook`.
6. Send `/status` command from an authorized Telegram account and verify responses plus OTEL traces in the collector dashboard.
