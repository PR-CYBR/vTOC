# Task Breakdown

## App Setup
- [ ] Draft Slack app manifest with scopes and event subscriptions.
- [ ] Secure admin approval and rotate credentials into secret store.

## Events Listener
- [ ] Implement `/slack/events` endpoint with signature verification and retry/backoff.
- [ ] Add local tunnel tooling for development.

## Message Processing
- [ ] Design Supabase schema and migrations for telemetry storage.
- [ ] Implement processors for message, reaction, and thread events.
- [ ] Integrate ChatKit alerting for priority events.

## Commands & Interactions
- [ ] Build `/vtoc-status` and `/vtoc-help` slash commands.
- [ ] Add interactive acknowledgement flows with buttons/modals.

## Quality & Operations
- [ ] Write integration tests using recorded Slack payloads.
- [ ] Instrument OTEL spans and metrics.
- [ ] Publish runbooks and execute staging rehearsal.
