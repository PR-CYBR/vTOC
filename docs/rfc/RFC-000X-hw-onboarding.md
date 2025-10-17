# RFC-000X: Station Hardware Onboarding Playbook

| Field | Value |
| --- | --- |
| Status | Draft |
| Authors | vTOC Core Team |
| Created | 2024-05-22 |
| Target Release | Rolling |

## Summary

This RFC standardizes the hardware onboarding path for vTOC stations. It documents how the FastAPI backend, AgentKit
connectors, and the React mission console collaborate with the new hardware provisioning wizard and telemetry feeds. The
intent is to give operations teams a single reference that bridges the developer documentation with on-site installation
checklists and diagrams.

## Motivation

Station operators currently rely on disparate notes to provision ADS-B receivers, GPS references, and H4M (Handheld for
Mission) tablets. This RFC aggregates the existing automation, shows how the bootstrap wizard hydrates secrets, and maps
out the telemetry surfaces that power the Leaflet overlays in the frontend.

## Architecture alignment

* The high-level system flow aligns with the diagrams maintained in [`docs/DIAGRAMS.md`](../DIAGRAMS.md), specifically the
  *Leaflet Mission Overlay* and *Hardware Provisioning Wizard* sections added for this effort.
* Hardware-specific flows reference the playbook notes in [`docs/HARDWARE.md`](../HARDWARE.md) and the individual
  connector guides (`ADSB.md`, `GPS.md`, and `H4M.md`).
* Deployment steps cross-link to [`docs/DEPLOYMENT.md`](../DEPLOYMENT.md) for container orchestration guidance and to the
  troubleshooting appendix in [`docs/QUICKSTART.md#troubleshooting`](../QUICKSTART.md#troubleshooting).

## Scope

The RFC covers:

1. The station bootstrap wizard (`python -m scripts.bootstrap_cli setup wizard`) and its interaction with generated
   `.env.station` files.
2. Physical installation requirements for the ADS-B antenna, GPS reference clock, and H4M tablets.
3. AgentKit connector expectations for telemetry payloads.
4. Operator-facing validation steps in the Leaflet mission console.

The RFC does not cover infrastructure provisioning (handled by [`docs/DEPLOYMENT.md`](../DEPLOYMENT.md)) or secret
rotation (see [`docs/secret-management.md`](../secret-management.md)).

## Onboarding workflow

1. **Pre-flight checks** — Follow [`docs/SETUP.md`](../SETUP.md) to confirm the station kit inventory, assign callsigns,
   and capture geospatial metadata.
2. **Wizard execution** — Run the bootstrap wizard (CLI or UI) to emit configuration for backend, agents, and frontend.
3. **Hardware bring-up** — Use the component guides in [`docs/HARDWARE.md`](../HARDWARE.md) to install, wire, and verify the
   ADS-B receiver, GPS timing module, and H4M tablets.
4. **Telemetry validation** — Confirm map tiles and overlays in the Leaflet console render the expected air tracks and
   mission markers. Refer to the Leaflet diagram for event-to-layer mappings.
5. **Handover** — Document findings in the station log and escalate anomalies through the troubleshooting matrix.

## Rollout plan

* Pilot the new wizard with two stations (Ops West and Intel East) before rolling out to all deployments.
* Capture feedback in the backlog under the `hardware-onboarding` label.
* Update automation scripts as the playbooks stabilize; the RFC will transition to "Accepted" once two successful station
  bring-ups are recorded without manual intervention.

## References

* [`docs/SETUP.md`](../SETUP.md)
* [`docs/HARDWARE.md`](../HARDWARE.md)
* [`docs/ADSB.md`](../ADSB.md)
* [`docs/GPS.md`](../GPS.md)
* [`docs/H4M.md`](../H4M.md)
* [`docs/DEPLOYMENT.md`](../DEPLOYMENT.md)
* [`docs/QUICKSTART.md#troubleshooting`](../QUICKSTART.md#troubleshooting)
