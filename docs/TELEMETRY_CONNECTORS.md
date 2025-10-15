# Telemetry Connector Guide

This guide explains how to configure telemetry ingestion across standalone agents and AgentKit playbooks. Each connector can run
in continuous mode, scheduled mode, or be triggered ad-hoc from ChatKit channels. Configuration lives in `agents/config/agents.yml`
and is shared with AgentKit via `agents/config/agentkit.yml`.

## Backend data model

The backend exposes `TelemetrySource`, `TelemetryEvent`, and `TelemetryThread` tables via Alembic migrations. Use the FastAPI
endpoints under `/api/v1/telemetry` to register sources, ingest readings, and query stored data:

| Endpoint | Description |
| --- | --- |
| `POST /api/v1/telemetry/sources` | Create or update telemetry source metadata for a station role. |
| `POST /api/v1/telemetry/ingest/{source}` | Push live readings from connectors, webhooks, or AgentKit playbooks. |
| `GET /api/v1/telemetry/events` | Retrieve stored telemetry with filtering by source, time, and station role. |
| `POST /api/v1/telemetry/events/{id}/thread` | Broadcast an event to the linked ChatKit thread. |

## Agent configuration template

```yaml
sources:
  <slug>:
    type: adsb|ais|aprs|tle|rtlsdr|meshtastic|gps|custom
    enabled: true
    schedule: "*/5 * * * *"   # cron or human shorthand (10m, 30s)
    mode: online|offline|chatkit
    station_role: ops|intel|logistics
    backend_url: "http://backend:8080"  # API root used by the agent
    chatkit_channel: "${STATION_CALLSIGN}"  # optional override per source
    broadcast: true   # send summaries to ChatKit threads when true
    # Source specific options...
```

### Schedule syntax

- `*/5 * * * *` — every 5 minutes
- `15m` — every 15 minutes
- `30s` — every 30 seconds
- `now` — run once immediately (used by ChatKit-triggered jobs)

When `mode: chatkit` is set the connector runs only when invoked by an AgentKit playbook.

## Connector catalog

Each connector supports both online (live) and offline (replay) scenarios. Optional fields enable ChatKit broadcasting and
AgentKit context injection.

### ADS-B (`adsb`)

- Online: provide `api_url` and optional `params`/`headers` for ADS-B providers. Use `chatkit_prompt_template` to customize AgentKit
  summaries.
- Offline: set `log_path` to JSON/CSV captures (e.g., `dump1090`).

### AIS (`ais`)

- Online: configure `api_url` plus `api_token` when required.
- Offline: specify `capture_path` pointing at `.nmea` logs.

### APRS (`aprs`)

- Online: set `igate_url` for APRS-IS or web APIs.
- Offline: provide `packet_log` referencing stored packets.

### TLE (`tle`)

- Online: define `tle_url` pointing at Celestrak or Space-Track feeds.
- Offline: set `tle_file` to a local TLE catalogue.

### RTL-SDR (`rtlsdr`)

- Online: use `stream_url` (e.g., `rtl_tcp://host:port`).
- Offline: set `iq_recording` to replay IQ captures.

### Meshtastic (`meshtastic`)

- Online: set `http_bridge` to the Meshtastic HTTP API endpoint.
- Offline: configure `json_log` to replay exported mesh telemetry.

### GPS (`gps`)

- Online: configure `ntrip_endpoint` for RTK/NTRIP casters or live GPS sources.
- Offline: provide `gpx_file` or `nmea_log` to replay recorded tracks.

### Custom connectors (`custom`)

- Provide a `module` path pointing at a Python callable inside `agents/connectors/`.
- Supply `options` for runtime configuration.
- When triggered from ChatKit, the AgentKit playbook will pass the prompt text under `context.prompt`.

## ChatKit + AgentKit integration

- When a ChatKit command mentions `@agent`, the backend dispatches the corresponding AgentKit playbook.
- Playbooks map to connector actions (`collect`, `analyze`, `broadcast`).
- Set `broadcast: true` to automatically post summaries back into the originating ChatKit thread.
- Use `chatkit_channel` to override the default station channel for long-running feeds.

## Database migrations

Alembic migrations are stored under `alembic/` and include the telemetry tables plus station role indices. Run them with:

```bash
alembic upgrade head
```

For role-specific databases the setup script executes migrations for each connection string derived from `DATABASE_URL`.
