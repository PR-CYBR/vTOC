# Station Setup Guide

This guide walks operators through the end-to-end onboarding sequence for a new vTOC station. It complements the
application-focused [`docs/QUICKSTART.md`](QUICKSTART.md) by emphasizing physical hardware preparation, configuration
capture, and validation checkpoints that must be completed before a station goes live.

## Prerequisites

* A validated station kit (see the inventory checklist below).
* Access to the station's ChatKit organization, AgentKit workspace, and the shared vTOC repository.
* Credentials required by the bootstrap wizard (ChatKit API key, AgentKit OAuth client, Supabase service key). Manage
  these secrets according to [`docs/secret-management.md`](secret-management.md).
* Deployment destination determined ahead of time. Use [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) to select between local,
  containerized, or Fly.io delivery.

## Inventory checklist

| Item | Notes | Linked Guide |
| --- | --- | --- |
| Ruggedized NUC / mini-PC | Hosts backend + connectors | [`docs/HARDWARE.md`](HARDWARE.md) |
| ADS-B receiver + antenna | Mounted with clear sky view | [`docs/ADSB.md`](ADSB.md) |
| GPS reference (USB or serial) | Provides timing + geofence | [`docs/GPS.md`](GPS.md) |
| H4M tablets (2+) | Mission console + offline cache | [`docs/H4M.md`](H4M.md) |
| PoE switch + cabling | Powers receivers / uplinks | [`docs/HARDWARE.md`](HARDWARE.md)#network |
| Station signage & labels | Callsign, role, and network IDs | [`docs/HARDWARE.md`](HARDWARE.md)#station-labelling |

Tick each row while inspecting shipments. Flag mismatches before proceeding to software tasks.

## Bootstrap workflow

1. **Clone and branch** — Pull the vTOC repository and create a per-station branch to capture configuration artifacts.
2. **Run health checks** — Execute the quick prerequisite checks from the README quick start (or run
   `python -m scripts.bootstrap_cli doctor`).
3. **Launch the wizard** — Start the guided setup via `python -m scripts.bootstrap_cli setup wizard`. The wizard asks for
   callsign, station role, geographic coordinates, and hardware serials. Export the resulting JSON for archival and load
   the generated `.env.station` file onto the target machine.
4. **Select deployment mode** — Use the prompts or reference [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) to choose between
   local development, Docker Compose, or Swarm/Fly.io rollouts.
5. **Distribute credentials** — Copy the `.env.*` files to the backend host, AgentKit runners, and tablets as instructed
   by the wizard. Validate checksums before powering devices.
6. **Record evidence** — Update the onboarding log in your operations tracker with screenshots of the wizard summary,
   photos of installed hardware, and copies of the generated configuration bundle.

## Validation

After installation and deployment:

* Confirm the backend `/healthz` endpoint returns `200` from the station subnet.
* Sign in to the frontend and verify Leaflet overlays display base map tiles. Refer to the *Leaflet Mission Overlay*
  diagram in [`docs/DIAGRAMS.md`](DIAGRAMS.md#leaflet-mission-overlay) for expected layers.
* Trigger an AgentKit smoke test (`python -m scripts.bootstrap_cli agents ping`) to confirm secrets are wired.
* Run through the troubleshooting matrix in [`docs/QUICKSTART.md#troubleshooting`](QUICKSTART.md#troubleshooting) if any
  checks fail. Escalate persistent faults to the deployment lead.

## Next steps

With the station validated, proceed to the component-specific guides (`ADSB.md`, `GPS.md`, `H4M.md`) to fine-tune telemetry
connectors and mission workflows. Keep the deployment guide open for rollback procedures and scaling patterns.
