# Research Notes

## Discord Platform
- Gateway connections require intents for guilds, guild messages, and message content (subject to privileged intent approval).
- Rate limit buckets vary by route; must inspect headers and respect `Retry-After` with jitter.
- Interaction responses must be acknowledged within 3 seconds; long tasks require deferred responses.

## Operational Considerations
- Bots need invite URLs with permissions (Send Messages, Manage Messages, Embed Links) defined in manifest.
- Sharding may be necessary if guild count grows; plan for `DISCORD_SHARD_COUNT` configuration.
- Investigate Discord's incident history to plan fallback strategies during outages.

## Security & Compliance
- Secrets stored in Fly.io and Compose should use environment variable names aligned with shared schema (`DISCORD_BOT_TOKEN`, `DISCORD_PUBLIC_KEY`).
- Audit trail for command invocations stored in Supabase; ensure data retention meets governance policies.
- Verify whether mission data requires redaction prior to sending to Discord (coordinate with compliance).
