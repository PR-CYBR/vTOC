# PR-CYBR Division Workflows

## Overview

This document outlines example mesh network deployments tailored for PR-CYBR operational divisions. Each workflow includes requirements analysis, technology selection, deployment procedures, and integration with vTOC.

## Division-Specific Deployments

### 1. Special Operations Division

**Mission Profile:**
- Small team operations (4-12 personnel)
- Urban/suburban environments
- 24-48 hour missions
- Covert/low-signature required

**Technology Stack:**
- **Tracking:** Trekker Mini GPS trackers (covert)
- **Comms:** LoRa mesh (low power signature)
- **Command:** Mobile vTOC station (vehicle-mounted Raspberry Pi 5)

**Deployment Workflow:**

1. **Pre-Mission Planning:**
   - Analyze AO (Area of Operations) terrain
   - Identify relay node locations (rooftops, elevated positions)
   - Calculate LoRa coverage (SF10-12 for reliability)
   
2. **Equipment Prep:**
   - Pre-configure LoRa nodes (network ID, encryption)
   - Charge all batteries (Trekker Mini: 4-7 days @ 1 min updates)
   - Test all units at staging area

3. **Deployment:**
   - Establish gateway at command vehicle
   - Deploy portable relay nodes (if needed for coverage)
   - Distribute Trekker Mini units to team members
   - Verify connectivity (all nodes check in)

4. **Operations:**
   - Real-time tracking on vTOC map
   - Text messaging via LoRa (low bandwidth)
   - Geofencing alerts (breach of AO boundaries)

5. **Exfiltration:**
   - Recover relay nodes
   - Download logs from all devices
   - Archive mission data in vTOC database

### 2. Search and Rescue Division

**Mission Profile:**
- Large area searches (10-100 km²)
- Mountainous/wilderness terrain
- 12-72 hour operations
- Multiple team coordination

**Technology Stack:**
- **Tracking:** LoRa MANET nodes (long range)
- **Comms:** LoRa + satellite fallback (Iridium)
- **Command:** Fixed TOC with vTOC backend
- **Aerial:** Spec5 Copilot drones for relay

**Deployment Workflow:**

1. **Pre-Mission:**
   - RadioMobile coverage analysis
   - Identify mountain peaks for relay nodes
   - Plan drone flight paths (aerial relay)

2. **Base Camp Setup:**
   - Establish TOC with vTOC backend
   - Deploy 2× gateway nodes (redundancy)
   - Setup StarLink or LTE for backhaul

3. **Field Deployment:**
   - Solar-powered relay nodes on peaks
   - LoRa nodes to SAR team members (SF12 max range)
   - Drones launched for dynamic relay (hover at optimal altitude)

4. **Search Operations:**
   - Real-time position tracking
   - Coverage map overlay (searched areas)
   - Alert system (target found, assistance needed)

5. **Post-Mission:**
   - Recover relay nodes
   - Generate search coverage report
   - Lessons learned (coverage gaps, relay performance)

### 3. Event Security Division

**Mission Profile:**
- Temporary event security (festivals, concerts, sports)
- 1-5 km² venue
- 8-72 hour operations
- High personnel density (50-200 security staff)

**Technology Stack:**
- **Tracking:** Mix of Trekker Bravo (supervisors) and LoRa (staff)
- **Surveillance:** IP cameras via WiFi HaLow bridges
- **Paxcounting:** LiLIGO ESP32 Paxcounters (crowd density)
- **Comms:** WiFi HaLow for high bandwidth (video)

**Deployment Workflow:**

1. **Pre-Event Survey:**
   - Site visit 1-2 weeks prior
   - Map venue, identify choke points
   - Plan camera and paxcounter locations

2. **Day-Before Setup:**
   - Deploy HaLow gateway at control center
   - Install HaLow relay nodes (perimeter poles)
   - Mount IP cameras with HaLow bridges
   - Position paxcounters at entrances/exits

3. **Event Operations:**
   - Live video feeds in vTOC control center
   - Real-time paxcount heatmap (crowd density)
   - GPS tracking of security patrols
   - Automated alerts (capacity exceeded, suspicious activity)

4. **Post-Event:**
   - Download all logs and video
   - Generate reports (peak crowd times, patrol coverage)
   - Pack and inventory equipment

### 4. Maritime Security Division

**Mission Profile:**
- Port facility security
- 5-10 km coverage area (waterfront + inland)
- 24/7 continuous operations
- Harsh environment (salt spray, wind)

**Technology Stack:**
- **Tracking:** Trekker Bravo (patrol boats, vehicles)
- **Sensors:** LoRa nodes (motion detectors, environmental)
- **Cameras:** WiFi HaLow (fixed positions)
- **Comms:** Redundant gateways with fiber backhaul

**Deployment Workflow:**

1. **Site Assessment:**
   - RF survey (multipath from metal containers)
   - Corrosion risk analysis
   - Power availability survey

2. **Infrastructure Installation:**
   - 2× redundant gateways (fiber to NOC)
   - 6-8 relay nodes (towers, buildings)
   - Hardened enclosures (IP67 minimum)
   - Marine-grade antennas (stainless hardware)

3. **Sensor Network:**
   - LoRa PIR sensors (perimeter fence)
   - Temperature sensors (container storage)
   - Cameras at gates, berths, fuel depot

4. **Operations:**
   - vTOC unified view (sensors, cameras, patrols)
   - Automated alerts (fence breach, anomaly detection)
   - Historical analysis (patrol patterns, incident correlation)

5. **Maintenance:**
   - Quarterly antenna inspection (corrosion)
   - Battery replacement schedule (harsh environment shortens life)
   - Firmware updates during maintenance windows

### 5. Disaster Response Division

**Mission Profile:**
- Rapid deployment (< 24 hours)
- Degraded infrastructure (no power, no internet)
- 50-500 km² affected area
- Multi-agency coordination

**Technology Stack:**
- **Tracking:** Mix of LoRa, Trekker (depending on cellular availability)
- **Comms:** LoRa mesh + satellite backhaul
- **Power:** Solar + battery for all nodes
- **Aerial:** Drones for initial assessment and relay

**Deployment Workflow:**

1. **Initial Response:**
   - Deploy fly-away TOC kit (Raspberry Pi 5, StarLink, solar)
   - Launch drones for aerial survey
   - Establish LoRa gateway at TOC

2. **Network Expansion:**
   - Portable relay nodes (battery + solar)
   - Position on high ground (buildings, hills)
   - Multi-hop mesh to cover affected area

3. **Coordination:**
   - Integrate with FEMA/Red Cross systems
   - Track responder teams (LoRa nodes)
   - Map damage assessments (drone footage + GPS)

4. **Sustained Operations:**
   - Solar keeps nodes operational (no grid power)
   - Daily battery checks (harsh conditions)
   - Adjust network as operations shift

5. **Recovery:**
   - Gradual transition to permanent infrastructure
   - Document deployment (lessons learned)
   - Recover and refurbish equipment

## Common Patterns

### Power Planning

**Solar Sizing:**
```
Daily Energy = Device Power (W) × Hours per Day
Battery Capacity (Wh) = Daily Energy × Days Autonomy × 1.5 (safety factor)
Solar Panel (W) = Daily Energy / (Peak Sun Hours × 0.7)
```

**Example: LoRa Relay Node**
- Power: 2W average
- Daily Energy: 2W × 24h = 48 Wh
- 3 days autonomy: 48 × 3 × 1.5 = 216 Wh → 18Ah @ 12V
- Solar (4 peak sun hours): 48 / (4 × 0.7) = 17W → Use 20W panel

### Frequency Coordination

**vTOC Recommended Band Plan:**
- **LoRa Primary:** 915.0-915.5 MHz
- **HaLow Primary:** 920.0-925.0 MHz
- **ADS-B:** 1090 MHz (receive only)
- **GPS:** 1575.42 MHz (receive only)
- **APRS (where licensed):** 144.39 MHz

**Separation:** Keep 5 MHz+ between LoRa and HaLow to minimize interference

### Redundancy Planning

**Critical Nodes:**
- Gateway: Deploy 2+ (different locations)
- Relay: Each edge node sees 2+ relay nodes
- Power: Battery backup for gateway (UPS)
- Backhaul: Primary + secondary WAN (Ethernet + LTE/StarLink)

## Integration with vTOC

All division deployments feed into centralized vTOC backend:

1. **Node Registration:**
   - Each device registered in vTOC database
   - Division tag, deployment ID, responsible party

2. **Real-Time Telemetry:**
   - Position updates (GPS)
   - Status updates (battery, signal strength)
   - Sensor data (temperature, motion, etc.)

3. **Map Visualization:**
   - Division-specific map layers
   - Color-coded by division/mission
   - Historical playback (mission review)

4. **Alerting:**
   - Automated alerts per division SOP
   - Escalation matrix (SMS, email, in-app)

5. **Reporting:**
   - After-action reports (automated)
   - Coverage analysis (where teams went)
   - Equipment utilization (battery life, uptime)

## Related Documentation

- [Mesh Planning Overview](OVERVIEW.md) - General planning methodology
- [LoRa Coverage Planning](LORA-COVERAGE.md) - LoRa deployment details
- [HaLow Coverage Planning](HALOW-COVERAGE.md) - WiFi HaLow details
- [Hardware Overview](../HARDWARE.md) - Equipment specifications

## Contributing

PR-CYBR divisions are encouraged to document their deployments and share lessons learned. Submit workflow updates via pull request or contact the vTOC maintainers.
