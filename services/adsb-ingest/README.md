# ADS-B Ingest Service

This service wraps [`readsb`](https://github.com/wiedehopf/readsb) or
`dump1090-fa` by providing:

* Environment-driven configuration rendering for RTL-SDR receivers.
* A lightweight FastAPI proxy that exposes the `aircraft.json` feed and
  forwards aircraft updates into the vTOC telemetry backend.
* Docker assets and mocks that simplify local development and testing.

## Components

| Path | Description |
| ---- | ----------- |
| `adsb_proxy/` | FastAPI application that polls `aircraft.json`, publishes a `/healthz` endpoint, and relays telemetry events. |
| `scripts/configure_readsb.py` | Renders configuration files for readsb/dump1090 using environment variables. |
| `templates/*.template` | Default templates for configuration rendering. |
| `tests/` | Unit tests and mock data for exercising the proxy. |

## Usage

Render a configuration file that points readsb at the correct RTL-SDR device:

```bash
python -m scripts.configure_readsb --target readsb --output /etc/readsb.conf \
  --template templates/readsb.conf.template
```

Then run the proxy:

```bash
uvicorn adsb_proxy.main:app --host 0.0.0.0 --port 8080
```

The proxy publishes:

* `GET /aircraft.json` — cached snapshot from readsb/dump1090.
* `GET /healthz` — health details consumed by `hw_status`.
* `GET /readyz` — readiness indicator for orchestration systems.

Telemetry events are pushed to the backend endpoint configured via the
`BACKEND_BASE_URL` and `TELEMETRY_ENDPOINT` environment variables.
