# Interactive vTOC Dashboard Features

This document describes the interactive features added to the vTOC dashboard.

## Map Component

The interactive map is built with [Leaflet](https://leafletjs.com/) and provides real-time geospatial visualization.

### Features

#### Base Map Switching
- **Streets View**: Dark-themed street map from CartoDB
- **Satellite View**: High-resolution satellite imagery from Esri

Toggle between views using the "BASE MAP" control in the top-right corner of the map.

#### Overlay Controls
- **Sensors**: Toggle sensor range overlays (UI ready for implementation)
- **Heatmap**: Toggle heatmap visualization (UI ready for implementation)

#### GeoJSON Import
1. Enter a URL to a GeoJSON file in the "IMPORT GEOJSON" input field
2. Click "Load" to fetch and display the data on the map
3. Features will be styled with cyan colors matching the dashboard theme
4. Click on features to view their properties in a popup

**Example GeoJSON URLs:**
- https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson
- https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson

### Technical Details

The Map component uses:
- **Next.js Dynamic Import**: Prevents SSR issues with Leaflet
- **React Hooks**: State management for layers and data
- **TypeScript**: Full type safety for map features
- **Responsive Design**: Adapts to different screen sizes

## Mission Console

The Mission Console provides simulated backend interactions for testing and demonstration.

### Features

#### Send Telemetry
1. Enter telemetry data or a message in the textarea
2. Click "📡 Send Telemetry"
3. A success notification will appear confirming submission
4. The data is logged to the browser console for debugging

**Use Cases:**
- Simulate sensor data submissions
- Test telemetry data formats
- Demonstrate real-time data ingestion workflows

#### Trigger Agent
1. Enter an agent command in the input field
2. Click "🤖 Trigger Agent" or press Enter
3. A success notification confirms the trigger
4. The command is logged to the console

**Use Cases:**
- Simulate GitHub Actions triggers
- Test agent command syntax
- Demonstrate automated workflow execution

#### Connection Status
The console displays a "Simulated Mode" status indicator with a pulsing yellow dot, indicating that backend connections are simulated for demonstration purposes.

### Toast Notifications

Actions in the Mission Console trigger toast notifications that:
- Appear in the top-right corner
- Auto-dismiss after 3 seconds
- Provide clear feedback on action success
- Stack vertically if multiple notifications occur

## Development

### Adding Real Backend Integration

To connect the Mission Console to a real backend:

1. **Telemetry Submission:**
```typescript
const handleTelemetrySend = async () => {
  const response = await fetch('/api/telemetry', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: telemetryMessage, timestamp: new Date().toISOString() })
  });
  // Handle response
};
```

2. **Agent Triggers:**
```typescript
const handleAgentTrigger = async () => {
  const response = await fetch('/api/agents/trigger', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: agentCommand, timestamp: new Date().toISOString() })
  });
  // Handle response
};
```

### Implementing Overlay Features

To add actual overlay functionality:

1. **Sensor Ranges:**
```typescript
// In Map.tsx, add sensor circle overlays
if (overlays.has('sensor-ranges')) {
  sensors.forEach(sensor => {
    L.circle([sensor.lat, sensor.lng], {
      radius: sensor.range,
      color: '#38bdf8',
      fillOpacity: 0.2
    }).addTo(mapInstanceRef.current!);
  });
}
```

2. **Heatmaps:**
```typescript
// Install leaflet.heat plugin and add heatmap layer
import 'leaflet.heat';

if (overlays.has('heatmap')) {
  const heatLayer = L.heatLayer(heatmapData, {
    radius: 25,
    blur: 15,
    maxZoom: 17
  }).addTo(mapInstanceRef.current!);
}
```

## Styling

All components use the existing dark theme:
- **Primary Background**: `#0f172a`
- **Accent Color**: `#38bdf8` (cyan)
- **Border Color**: `rgba(148, 163, 184, 0.25)`
- **Panel Background**: `rgba(15, 23, 42, 0.75)` with backdrop blur

Custom CSS classes are defined in `styles/globals.css` for:
- `.map-container`, `.map-controls`, `.map-control-btn`
- `.mission-console`, `.mission-form`, `.mission-btn`
- `.toast`, `.toast--success`, `.toast--info`

## Browser Compatibility

The interactive features are compatible with:
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

Note: Map tiles may be blocked by ad blockers. Disable ad blockers for full functionality.

## Performance

- Map tiles are loaded on-demand and cached by the browser
- GeoJSON rendering uses Leaflet's optimized Canvas renderer for large datasets
- Toast notifications are cleaned up automatically to prevent memory leaks
- The Map component properly cleans up on unmount to prevent Leaflet memory leaks

## Troubleshooting

### Map doesn't appear
- Check browser console for errors
- Verify network connectivity (tiles are loaded from external CDNs)
- Disable ad blockers that may block map tile requests

### GeoJSON won't load
- Verify the URL is accessible and returns valid GeoJSON
- Check CORS headers if loading from a different domain
- Ensure the GeoJSON structure is valid (use a validator like geojsonlint.com)

### Notifications don't appear
- Check if notifications are being blocked by browser settings
- Verify the console logs show the action was triggered
- Check for JavaScript errors in the browser console
