# vTOC Frontend

The frontend is a Vite + React + TypeScript application that renders mission maps, station dashboards, and the ChatKit mission
console. It consumes the FastAPI backend at `/api/v1/*` and uses `.env.station` to personalize the UI for each station role.

## Prerequisites

- Node.js 18+
- `pnpm` 8+
- Backend running locally at `http://localhost:8080` (or configure `VITE_API_URL`)

## Installation

```bash
pnpm install
```

If you ran `make setup-local`, the dependency installation is handled automatically. The generated `.env.station` file is read by
Vite at startup.

## Development

```bash
pnpm dev
```

The dev server runs on http://localhost:5173 by default. Hot module replacement is enabled. Ensure the backend environment files
have `STATION_CALLSIGN` and `POSTGRES_STATION_ROLE` so the UI can render the proper badge and mission filters.

## Testing

```bash
pnpm test
```

Vitest executes in CI mode by default (see `make frontend-test`). Add focused tests with `pnpm test -- --watch` while developing.

## Build

```bash
pnpm build
```

The build output lands in `dist/` and is consumed by the nginx-based container image published to GHCR.

## Environment variables

- `VITE_API_URL` — override backend base URL (defaults to `http://localhost:8080`).
- `VITE_STATION_CALLSIGN` — set automatically from `.env.station`.
- `VITE_STATION_ROLE` — used to scope mission widgets and ChatKit thread filters.
- `VITE_CHATKIT_API_KEY` — enables the embedded ChatKit console when paired with the variables below.
- `VITE_AGENTKIT_ORG_ID` — organization identifier passed to ChatKit for routing agent actions.
- `VITE_CHATKIT_WIDGET_URL` — URL of the ChatKit web component bundle to hydrate the console UI.
- `VITE_AGENTKIT_DEFAULT_STATION_CONTEXT` — optional override for the default station context shared with ChatKit (defaults to `toc-s1`).
- `VITE_CHATKIT_TELEMETRY_CHANNEL` — optional telemetry channel name used to scope real-time event streams.

Refer to [`docs/QUICKSTART.md`](../docs/QUICKSTART.md) for the station bootstrap workflow and to [`CONTRIBUTING.md`](../CONTRIBUTING.md)
for testing expectations.
