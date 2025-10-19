# Quickstart

1. Install dependencies: `pnpm install` and build shared runtime `pnpm --filter bot-shared build`.
2. Create `.env.discord` with `DISCORD_BOT_TOKEN`, `DISCORD_PUBLIC_KEY`, `DISCORD_APP_ID`, and optional `DISCORD_GUILD_ID` for development registration.
3. Start local dependencies: `docker compose up chatkit-server agentkit supabase`.
4. Register slash commands for the development guild: `pnpm --filter bot-discord run register-commands --env-file .env.discord`.
5. Launch the bot locally: `pnpm --filter bot-discord dev -- --env-file .env.discord` and invite it to the target guild.
6. Execute `/mission` and `/diagnostics` commands; verify responses, OTEL spans, and Supabase audit entries.
