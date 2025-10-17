# GPS Timing & Geofence Guide

The GPS module provides precise timing for telemetry correlation and enforces the station geofence used by AgentKit playbooks.
Pair this guide with [`docs/SETUP.md`](SETUP.md) and [`docs/HARDWARE.md`](HARDWARE.md) when preparing a station.

## Placement

* Install the GPS puck with clear sky view; south-facing windows are acceptable if outdoor mounting is not possible.
* Maintain >1 m separation from the ADS-B antenna to prevent interference.
* Route cabling away from high-voltage lines or radio transmitters.

## Connection options

| Interface | Notes |
| --- | --- |
| USB | Plug-and-play on Linux. Exposes `/dev/ttyACM*` device nodes. |
| Serial (RS-232) | Requires USB adapter. Set baud to 9600 8N1 unless vendor recommends otherwise. |
| PPS | Optional SMA lead for pulse-per-second timing into supported compute nodes. |

## Software setup

1. Install `gpsd` (`sudo apt install gpsd gpsd-clients`).
2. Update `/etc/default/gpsd` to point at the detected device (`DEVICES="/dev/ttyACM0"`). Enable `USBAUTO="true"` for hotplug.
3. Restart the service (`sudo systemctl restart gpsd`).
4. Verify lock status with `cgps -s`. Time-to-first-fix should be <90 seconds outdoors.
5. Export coordinates to the bootstrap wizard if the station relocates. Update `.env.station` and redeploy.

## Integration with vTOC

* The backend reads GPS time from `telemetry.gpsd`. Ensure the connector is enabled via the wizard or update
  `scripts/inputs.schema.json` accordingly.
* AgentKit playbooks use the geofence radius to trigger alerts when tracked assets depart the assigned bubble.
* Leaflet overlays display the geofence ring. See [`docs/DIAGRAMS.md#leaflet-mission-overlay`](DIAGRAMS.md#leaflet-mission-overlay)
  for the visualization.

## Troubleshooting

* If `cgps` shows `?` for coordinates, inspect antenna placement and cabling.
* Validate that `/etc/ntp.conf` references `127.127.28.0` (gpsd SHM). Restart `systemd-timesyncd` if NTP refuses to sync.
* Follow the escalation steps in [`docs/QUICKSTART.md#troubleshooting`](QUICKSTART.md#troubleshooting) for persistent time
  drift.
