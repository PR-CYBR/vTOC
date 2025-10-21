# Research Notes

## Slack Platform
- Events API requires responding within 3 seconds; long processing must be deferred to background workers.
- Socket Mode is an alternative but webhook-based Events API aligns better with Fly.io routing.
- Rate limits vary per method; bulk message posting must honor `Retry-After` headers.

## Data Handling
- Supabase schema needs channel metadata and message fingerprints to prevent duplicates.
- ChatKit notifications should include origin channel and message link for context.
- Evaluate whether message retention policies impact historical telemetry needs.

## Security & Compliance
- Signing secret rotation schedule should align with Slack admin policies.
- Ensure sensitive messages flagged by DLP are not persisted without encryption or additional controls.
- Confirm whether workspace requires audit logs for slash command invocations.
