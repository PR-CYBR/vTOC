# Slack Events Contract

## Purpose
Define how Slack channel activity translates into telemetry events and notifications consumed by downstream services.

## Event Intake
- All Events API requests must include valid signatures verified with Slack signing secret.
- Acknowledge events within 3 seconds; processing beyond that must be queued asynchronously.
- Maintain idempotency by tracking `event_id` in Supabase to avoid duplicate processing.

## Normalization Schema
- `event_type`: e.g., `message.posted`, `message.reaction`, `message.thread_reply`.
- `channel_id`, `channel_name`, `workspace_id` metadata.
- `actor_id`, `actor_display_name`, `actor_role` derived from Slack profile fields.
- `payload`: JSON blob with sanitized message text and attachments.
- `detected_signals`: keywords, mentions, or anomalies identified by processors.

## Notification Rules
- High-severity signals trigger ChatKit notifications containing channel permalink and summary.
- Duplicate alerts suppressed for 10 minutes per unique signal to prevent spam.
- Slash command responses should include correlation IDs referencing telemetry records.

## Compliance Requirements
- Respect Slack retention rules by redacting messages flagged by DLP policies.
- Provide deletion API to remove telemetry records upon workspace admin request.
- Log administrative actions (credential rotation, manifest changes) to central audit trail.
