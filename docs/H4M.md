# H4M Tablet Guide

H4M (Handheld for Mission) tablets provide mobile access to the vTOC mission console and offline checklists. This guide
covers provisioning, offline cache management, and operator handoff.

## Device preparation

* Use ruggedized Android or iPadOS devices with at least 64 GB storage and LTE capability.
* Apply a tempered glass screen protector and waterproof case. Label the case with station callsign and tablet number.
* Enroll devices in your MDM solution with a dedicated `vtoc-h4m` profile.

## Application install

1. Install the latest vTOC mobile wrapper or configure the browser in kiosk mode pointing to the station URL (e.g.,
   `https://station-ops.example.com`).
2. Import the `.env.station` values produced by the wizard into the MDM as managed app config so the tablet knows which
   station role and callsign to display.
3. Sync bookmarks to the troubleshooting matrix and deployment guide for quick operator access.

## Offline cache

* Enable service worker caching in the mission console (toggle located under **Settings → Offline cache**).
* Initiate an initial sync over Wi-Fi before handing devices to the field.
* Schedule weekly refreshes; the cache expires after 14 days to avoid stale map tiles.

## Operational checklist

* Verify LTE or Wi-Fi connectivity before each mission. Capture screenshots of the network status indicator.
* Confirm Leaflet overlays render the ADS-B layer and geofence ring. Reference [`docs/DIAGRAMS.md#leaflet-mission-overlay`](DIAGRAMS.md#leaflet-mission-overlay).
* Run the built-in diagnostics (**Settings → Run checks**) to validate API reachability and AgentKit webhook health.
* Escalate issues using the procedures in [`docs/QUICKSTART.md#troubleshooting`](QUICKSTART.md#troubleshooting).

## Security

* Enforce biometric unlock and automatic device wipe after 10 failed attempts.
* Use per-operator accounts tied to SSO. Revoke access when roles change or devices are lost.
* Keep firmware patched; schedule quarterly reviews aligned with the maintenance windows in [`docs/HARDWARE.md`](HARDWARE.md#maintenance).
