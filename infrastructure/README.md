# Infrastructure Overview

The `infrastructure/` directory contains automation for provisioning backing services and
supplemental assets that operators deploy alongside vTOC. This document highlights the
telemetry ingest additions introduced for the GPS, ADS-B, and H4M bridge services.

## Terraform secrets and variables

Terraform templates under `infrastructure/terraform/` expose variables that are mapped to
runtime secrets via `secrets.tf`. In addition to the existing backend and frontend
configuration, the following variables drive the new telemetry ingest containers:

| Variable | Description | Default |
| --- | --- | --- |
| `gps_serial_device` | Serial device path exposed to the GPS ingest container. | `/dev/ttyUSB0` |
| `gps_baud_rate` | Baud rate for the GPS serial device. | `9600` |
| `gps_source_slug` | Telemetry source slug recorded by the GPS ingest service. | `station-gps` |
| `adsb_feed_url` | URL for retrieving ADS-B JSON feeds (e.g., dump1090). | `http://dump1090:8080/data/aircraft.json` |
| `adsb_source_slug` | Telemetry source slug recorded by the ADS-B ingest service. | `station-adsb` |
| `rtlsdr_device_serial` | Optional RTL-SDR serial number to pin the USB receiver. | _(empty)_ |
| `h4m_serial_device` | Serial device path exposed to the H4M bridge container. | `/dev/ttyUSB1` |
| `h4m_baud_rate` | Baud rate for the H4M bridge serial interface. | `115200` |
| `h4m_channel` | Channel identifier announced to the backend by the H4M bridge. | `station-h4m` |
| `h4m_source_slug` | Telemetry source slug recorded by the H4M bridge service. | `station-h4m` |

When `terraform output -json fly_secret_map` is rendered these keys are now included,
allowing operators to push consistent secrets into Fly.io or other target platforms.
Override any value within `terraform.tfvars` or environment-specific tfvars files.

### Mission timeline configuration

The backend exposes a `timeline_event_limit` variable that caps the number of mission
timeline events returned in API responses. Adjust the default of `100` to trim payloads or
increase retention when exporting telemetry. The value is surfaced to Fly.io as the
`MISSION_TIMELINE_LIMIT` secret so runtime deployments stay aligned with Terraform state.

## Udev rules for telemetry devices

Udev rules under `deploy/udev/99-vtoc.rules` grant non-root access to USB serial adapters
and RTL-SDR receivers commonly used by the ingest services. Operators may add additional
rules under `/etc/udev/rules.d/99-vtoc-local.rules` to tailor permissions for unique
hardware revisions without modifying the shared rule set.
