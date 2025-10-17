# ADS-B Receiver Guide

The ADS-B receiver provides air track telemetry that populates the Leaflet airspace overlay in the mission console. Use this
guide alongside [`docs/SETUP.md`](SETUP.md) and the troubleshooting resources in
[`docs/QUICKSTART.md#troubleshooting`](QUICKSTART.md#troubleshooting).

## Hardware placement

* Mount the antenna outdoors with 360° line of sight. Roof mounts should extend at least 0.5 m above nearby obstacles.
* Use low-loss coax (LMR-400 or better) for runs longer than 10 m. Avoid kinks and secure with UV-resistant ties.
* Keep the receiver enclosure within -20°C to 50°C. If deployed in extreme climates, add a weatherproof housing with
  passive ventilation.

## Wiring

1. Connect the antenna feedline to the receiver's SMA port.
2. Attach PoE or 12 V power as supplied in the kit.
3. Plug Ethernet into the sensor VLAN configured per [`docs/HARDWARE.md`](HARDWARE.md#network).
4. Verify link lights and that the receiver leases an IP from the reserved DHCP scope.

## Software configuration

* Access the receiver web UI (usually `http://<receiver-ip>/`). Set the station callsign and GPS coordinates captured in
  the onboarding wizard.
* Enable JSON or Beast data feeds. The AgentKit ADS-B connector supports:

  | Protocol | Port | Notes |
  | --- | --- | --- |
  | Beast | 30005 | Default raw stream for dump1090-compatible receivers |
  | JSON  | 30047 | Structured payload used by `telemetry.adsb` connector |

* Configure a push target to the backend ingress (e.g., `http://<station-host>:8080/api/v1/telemetry/adsb`). Use HTTPS if
  the deployment is exposed externally; reference [`docs/DEPLOYMENT.md`](DEPLOYMENT.md#ingress) for TLS options.

## Validation

* Run `python -m scripts.bootstrap_cli telemetry adsb --check` from the compute node. The command pings the receiver and
  validates schema compatibility.
* Open the Leaflet mission console and confirm new aircraft tracks appear within 60 seconds. See the diagram in
  [`docs/DIAGRAMS.md#leaflet-mission-overlay`](DIAGRAMS.md#leaflet-mission-overlay) for expected layer behavior.
* If tracks fail to populate, consult the networking section in [`docs/HARDWARE.md`](HARDWARE.md#network) and the
  troubleshooting checklist in [`docs/QUICKSTART.md`](QUICKSTART.md#troubleshooting).

## Maintenance

* Update receiver firmware semi-annually. Record version numbers in your station log.
* Inspect antenna mounts quarterly for corrosion or loosened hardware.
* Rotate spare antennas yearly to maintain cable integrity.
