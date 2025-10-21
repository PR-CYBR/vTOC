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

## Udev rules for telemetry devices

Udev rules under `deploy/udev/99-vtoc.rules` grant non-root access to USB serial adapters
and RTL-SDR receivers commonly used by the ingest services. The Ansible deployment
playbook now copies this rule into `/etc/udev/rules.d/99-vtoc.rules` and triggers a
`udevadm control --reload` so that new permissions are active immediately. Stations that
need hardware-specific tweaks can override the `vtoc_udev_rule_src` Ansible variable (for
example within `inventory.ini`, `group_vars/`, or `host_vars/`) to point at a station
specific file while retaining the shared automation. Additional local rules may still be
added under `/etc/udev/rules.d/99-vtoc-local.rules` to tailor permissions for unique
hardware revisions without modifying the shared rule set.
