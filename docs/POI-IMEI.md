# POI and IMEI Tracking Guide

This document explains how operators configure and use the Person-of-Interest (POI) tracking and IMEI-based alerting system in vTOC.

## Overview

The POI/IMEI tracking system allows operators to:

1. **Manage Persons of Interest**: Track individuals, vehicles, or devices with multiple identifiers
2. **IMEI Watchlists**: Maintain whitelists and blacklists of device IMEIs
3. **Automatic Alerts**: Receive real-time alerts when tracked IMEIs appear in telemetry
4. **Timeline Integration**: View alerts in the station timeline with full POI context
5. **Mission Logging**: Get ChatKit notifications for critical IMEI hits

## Core Concepts

### Person of Interest (POI)

A POI represents an entity being tracked. Each POI has:

- **Name**: Human-readable identifier (e.g., "Suspect Vehicle Alpha")
- **Category**: Type of entity (`person`, `vehicle`, `device`)
- **Risk Level**: Assessment level (`info`, `watch`, `hostile`)
- **Notes**: Additional context or intelligence
- **Identifiers**: One or more identifiers (IMEI, MAC, callsign, phone)
- **Status**: Active or inactive tracking

### IMEI Watchlist

The IMEI watchlist provides fine-grained device tracking:

- **Identifier Value**: The IMEI number (15 digits)
- **List Type**: Either `whitelist` or `blacklist`
  - **Blacklist**: High-priority alerts for unauthorized/hostile devices
  - **Whitelist**: Tracking of known-friendly devices
- **Label**: Short description of the device
- **Linked POI**: Optional association with a POI record

### Alert Types

When telemetry contains a watched IMEI:

- **Blacklist Hit** (`imei_blacklist_hit`): High-severity alert requiring immediate attention
- **Whitelist Sighting** (`imei_whitelist_seen`): Informational tracking event

## API Operations

### Managing POIs

#### List POIs
```bash
GET /api/v1/poi
GET /api/v1/poi?is_active=true
```

#### Create POI
```bash
POST /api/v1/poi
Content-Type: application/json

{
  "name": "Hostile UAV",
  "category": "device",
  "risk_level": "hostile",
  "notes": "Unidentified drone near restricted airspace",
  "is_active": true
}
```

#### Get POI Details
```bash
GET /api/v1/poi/{poi_id}
```

#### Update POI
```bash
PATCH /api/v1/poi/{poi_id}
Content-Type: application/json

{
  "risk_level": "watch",
  "notes": "Confirmed as training asset"
}
```

#### Delete POI
```bash
DELETE /api/v1/poi/{poi_id}
```

### Managing POI Identifiers

#### Add Identifier to POI
```bash
POST /api/v1/poi/{poi_id}/identifiers
Content-Type: application/json

{
  "poi_id": 1,
  "identifier_type": "imei",
  "identifier_value": "123456789012345",
  "is_primary": true
}
```

Supported identifier types:
- `imei`: Device IMEI
- `mac`: MAC address
- `callsign`: Radio callsign
- `phone`: Phone number

#### List POI Identifiers
```bash
GET /api/v1/poi/{poi_id}/identifiers
```

#### Delete Identifier
```bash
DELETE /api/v1/poi/{poi_id}/identifiers/{identifier_id}
```

### Managing IMEI Watchlist

#### List Watchlist Entries
```bash
GET /api/v1/imei-watchlist
GET /api/v1/imei-watchlist?list_type=blacklist
```

#### Add IMEI to Watchlist
```bash
POST /api/v1/imei-watchlist
Content-Type: application/json

{
  "identifier_value": "123456789012345",
  "list_type": "blacklist",
  "label": "Unauthorized Device",
  "linked_poi_id": 1
}
```

#### Get Watchlist Entry
```bash
GET /api/v1/imei-watchlist/{entry_id}
```

#### Check IMEI Status
```bash
GET /api/v1/imei-watchlist/check/{imei}
```

Returns the watchlist entry if found, or `null` if not on list.

#### Update Watchlist Entry
```bash
PATCH /api/v1/imei-watchlist/{entry_id}
Content-Type: application/json

{
  "list_type": "whitelist",
  "label": "Cleared Device"
}
```

#### Delete Watchlist Entry
```bash
DELETE /api/v1/imei-watchlist/{entry_id}
```

## Telemetry Integration

### IMEI Format in Telemetry

Telemetry events can include IMEI in the payload:

```json
{
  "source_slug": "rf-sensor-1",
  "event_time": "2024-11-13T12:00:00Z",
  "payload": {
    "imei": "123456789012345",
    "device_type": "mobile",
    "signal_strength": -75
  }
}
```

The system checks both `payload.imei` and `payload.IMEI` (case-insensitive).

### Alert Enrichment

When an IMEI matches a watchlist entry, the telemetry event is automatically enriched:

```json
{
  "status": "imei_blacklist_hit",
  "payload": {
    "imei": "123456789012345",
    "imei_watchlist_hit": true,
    "imei_list_type": "blacklist",
    "poi_id": 1,
    "poi_name": "Hostile UAV",
    "poi_risk_level": "hostile",
    "device_type": "mobile",
    "signal_strength": -75
  }
}
```

### Timeline Representation

POI/IMEI alerts appear in the station timeline as distinct entries:

```json
{
  "entry_type": "poi_imei_alert",
  "occurred_at": "2024-11-13T12:00:00Z",
  "event_id": 456,
  "alert_type": "imei_blacklist_hit",
  "imei": "123456789012345",
  "poi_id": 1,
  "poi_name": "Hostile UAV",
  "station_callsign": "TOC-S1",
  "payload": { /* full event data */ }
}
```

## Frontend Operations

### POI Management UI

1. **Navigate to Admin Panel** → **POI Management**
2. **Create New POI**:
   - Enter name, category, and risk level
   - Add descriptive notes
   - Click **Create**
3. **Add Identifiers**:
   - Select POI from list
   - Click **Add Identifier**
   - Enter identifier type and value
   - Mark as primary if applicable
4. **Update Risk Level**:
   - Click POI name
   - Adjust risk level as intelligence develops
   - Save changes

### IMEI Watchlist UI

1. **Navigate to Admin Panel** → **IMEI Watchlist**
2. **Add IMEI Entry**:
   - Enter IMEI value (15 digits)
   - Select **Blacklist** or **Whitelist**
   - Add descriptive label
   - Optionally link to existing POI
3. **View Watchlist**:
   - Filter by list type
   - Search by IMEI or label
4. **Update Entry**:
   - Click entry to edit
   - Change list type or label
   - Link/unlink POI

### Viewing Alerts

#### Timeline View

1. **Navigate to Station** → **Timeline**
2. **Filter by Alert Type**:
   - **POI Only**: Show only POI-related events
   - **Blacklist Hits**: High-priority alerts
   - **Whitelist Sightings**: Known device tracking
3. **Alert Indicators**:
   - 🔴 Red icon for blacklist hits
   - 🟢 Green icon for whitelist sightings
   - POI name shown in alert header
4. **View Details**:
   - Click alert for full context
   - See IMEI, POI info, timestamp
   - Access raw telemetry data

#### Map View

POI/IMEI alerts with location data appear on the map:

- **Blacklist hits**: Red marker with alert icon
- **Whitelist sightings**: Blue marker with tracking icon
- **Hover**: Shows POI name and IMEI
- **Click**: Opens detail panel

## ChatKit Integration

### Automatic Notifications

When a blacklist hit occurs, ChatKit receives a mission log message:

```
🚨 IMEI BLACKLIST ALERT
IMEI: 123456789012345
POI: Hostile UAV (hostile)
Station: TOC-S1
Time: 2024-11-13 12:00:00 UTC
Location: 34.0522°N, 118.2437°W
```

Whitelist sightings generate informational messages:

```
✓ IMEI Whitelist Sighting
IMEI: 987654321098765
POI: Friendly Asset Alpha (info)
Station: TOC-S2
Time: 2024-11-13 12:05:00 UTC
```

### Manual Queries

Operators can query POI/IMEI status via ChatKit commands:

- `@agent check imei 123456789012345` - Check if IMEI is on watchlist
- `@agent list poi` - List active POIs
- `@agent poi status "Hostile UAV"` - Get POI details

## Operational Workflows

### Scenario 1: New Threat Identification

1. Intelligence identifies hostile device with IMEI `123456789012345`
2. Create POI:
   - Name: "Hostile Drone Alpha"
   - Category: device
   - Risk Level: hostile
3. Add IMEI identifier to POI
4. Add IMEI to blacklist with label "Unauthorized UAV"
5. System automatically alerts on future detections
6. ChatKit notifies all station operators

### Scenario 2: Friendly Asset Tracking

1. Deploy friendly asset with IMEI `987654321098765`
2. Create POI:
   - Name: "Blue Force Tracker #5"
   - Category: device
   - Risk Level: info
3. Add IMEI to whitelist
4. Monitor asset location via timeline whitelist sightings
5. Track movement on map view

### Scenario 3: Escalating Threat

1. Device initially on whitelist (suspected friendly)
2. Intelligence update reveals hostile intent
3. Update POI risk level: info → watch → hostile
4. Move IMEI from whitelist to blacklist
5. System immediately escalates future detections
6. Historical timeline shows risk progression

## Best Practices

### POI Management

- Use descriptive names that are meaningful to all operators
- Update risk levels as intelligence develops
- Add comprehensive notes with sources and dates
- Mark primary identifiers for quick reference
- Deactivate POIs when no longer relevant (don't delete for audit trail)

### IMEI Watchlists

- Verify IMEI format (15 digits) before adding
- Use blacklist for unauthorized/hostile devices
- Use whitelist for friendly asset tracking
- Link IMEIs to POIs when entity is identified
- Regular review and cleanup of stale entries

### Timeline Monitoring

- Enable POI filter during high-threat operations
- Configure alert thresholds for blacklist hits
- Review whitelist sightings for anomalies
- Correlate alerts with other intelligence sources

### ChatKit Usage

- Monitor ChatKit for immediate blacklist alerts
- Use manual queries for on-demand status checks
- Document alert responses in mission logs
- Escalate critical alerts to command

## Security Considerations

- POI/IMEI data is sensitive intelligence
- Access restricted to authorized operators
- All POI/IMEI operations are audited
- Watchlist changes are logged with user context
- Regular review of access permissions

## Troubleshooting

### IMEI Not Detected

- Verify IMEI format in telemetry payload
- Check payload uses `imei` or `IMEI` key
- Ensure telemetry source properly extracts IMEI
- Confirm watchlist entry exists and is active

### Missing Alerts

- Verify POI is active (`is_active: true`)
- Check IMEI is on correct list (blacklist/whitelist)
- Confirm station role has proper permissions
- Review telemetry source configuration

### Timeline Not Showing Alerts

- Refresh timeline view
- Clear POI filter if applied
- Check event occurred within timeline date range
- Verify station_id matches in telemetry event

### ChatKit Notifications Not Arriving

- Confirm ChatKit webhook configuration
- Check `CHATKIT_API_KEY` and `CHATKIT_ORG_ID` env vars
- Verify station callsign matches ChatKit channel
- Review backend logs for webhook errors

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Telemetry Connectors](TELEMETRY_CONNECTORS.md)
- [Station Timeline](QUICKSTART.md#station-timeline-ui)
- [ChatKit Integration](ARCHITECTURE.md#chatkit--agentkit-workflow)
