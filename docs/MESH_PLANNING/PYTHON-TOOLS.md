# Python Planning Tools

## Overview

The vTOC repository includes Python utilities for RF and mesh network planning. These tools help calculate link budgets, coverage areas, and optimize node placement.

## Installation

```bash
cd /home/runner/work/vTOC/vTOC
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/rf_planning/requirements.txt
```

## Link Budget Calculator

Calculate received signal strength and link margin:

```python
from scripts.rf_planning.link_budget import LinkBudget

# Example: 915 MHz LoRa link
link = LinkBudget(
    freq_mhz=915,
    distance_km=5,
    tx_power_dbm=20,
    tx_ant_gain_dbi=5,
    rx_ant_gain_dbi=5,
    cable_loss_db=2,
    misc_loss_db=3  # Weather, foliage, etc.
)

print(f"Free Space Path Loss: {link.fspl_db:.1f} dB")
print(f"Total Path Loss: {link.total_path_loss_db:.1f} dB")
print(f"Received Power: {link.rx_power_dbm:.1f} dBm")

# For LoRa with RX sensitivity -130 dBm
rx_sensitivity = -130
link_margin = link.rx_power_dbm - rx_sensitivity
print(f"Link Margin: {link_margin:.1f} dB")
```

## Coverage Area Estimator

Generate coverage polygons for mapping:

```python
from scripts.rf_planning.coverage import CoverageArea
import json

# Define transmitter
area = CoverageArea(
    center_lat=42.3601,
    center_lon=-71.0589,
    freq_mhz=915,
    tx_power_dbm=20,
    ant_gain_dbi=5,
    ant_height_m=10,
    rx_sensitivity_dbm=-110,
    environment='suburban'  # rural, suburban, urban, dense_urban
)

# Generate GeoJSON coverage polygon
geojson = area.to_geojson()

# Save for vTOC map visualization
with open('coverage.geojson', 'w') as f:
    json.dump(geojson, f, indent=2)
```

## Fresnel Zone Calculator

Check if path has adequate clearance:

```python
from scripts.rf_planning.fresnel import FresnelZone

fz = FresnelZone(
    freq_mhz=915,
    distance_km=5,
    tx_height_m=10,
    rx_height_m=10,
    terrain_profile=[0, 5, 10, 8, 5, 0]  # Heights in meters along path
)

# Check clearance
clearance_percent = fz.calculate_clearance()
print(f"Fresnel Zone Clearance: {clearance_percent:.0f}%")

if clearance_percent >= 60:
    print("✓ Link has adequate clearance")
else:
    print("⚠ Link may be obstructed, consider raising antennas")
```

## Mesh Network Optimizer

Optimize node placement for coverage:

```python
from scripts.rf_planning.mesh_optimizer import MeshOptimizer

# Define area and requirements
optimizer = MeshOptimizer(
    area_bounds=[(42.35, -71.06), (42.37, -71.04)],  # SW, NE corners
    coverage_radius_km=2,
    min_redundancy=2  # Each point covered by 2+ nodes
)

# Add candidate node locations
candidates = [
    {'lat': 42.36, 'lon': -71.05, 'height_m': 10, 'type': 'gateway'},
    {'lat': 42.365, 'lon': -71.055, 'height_m': 6, 'type': 'relay'},
    # ... more candidates
]

optimizer.add_candidates(candidates)

# Optimize (select minimum nodes for coverage)
selected_nodes = optimizer.optimize()

# Export results
optimizer.export_geojson('optimized_mesh.geojson')
print(f"Selected {len(selected_nodes)} nodes for 95% coverage")
```

## Elevation Profile Tool

Analyze terrain between two points:

```python
from scripts.rf_planning.elevation import ElevationProfile

# Requires SRTM elevation data (download from USGS)
profile = ElevationProfile(
    start_lat=42.3601,
    start_lon=-71.0589,
    end_lat=42.3650,
    end_lon=-71.0520,
    data_source='srtm'  # SRTM elevation data
)

# Plot elevation along path
profile.plot(filename='elevation_profile.png')

# Check for obstructions
obstructed = profile.check_line_of_sight(
    tx_height_m=10,
    rx_height_m=10,
    freq_mhz=915
)

if not obstructed:
    print("✓ Clear line of sight")
else:
    print("⚠ Obstructed path")
```

## Related Documentation

- [Mesh Planning Overview](OVERVIEW.md) - Planning methodology
- [LoRa Coverage Planning](LORA-COVERAGE.md) - LoRa-specific planning
- [HaLow Coverage Planning](HALOW-COVERAGE.md) - WiFi HaLow planning

## Future Development

The Python planning tools are under active development. Planned features:

- Integration with OpenStreetMap for building heights
- Automated waypoint generation for site surveys
- Multi-objective optimization (cost vs. coverage)
- 3D visualization with terrain
- Export to common RF planning formats (KMZ, etc.)

Contributions welcome! See `scripts/rf_planning/README.md` for development guidelines.
