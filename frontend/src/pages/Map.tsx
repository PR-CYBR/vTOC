import { useMemo, useState } from 'react';
import { MapContainer, Marker, TileLayer, Tooltip, LayerGroup, CircleMarker } from 'react-leaflet';
import type { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { useStationDashboard, useTelemetryEvents } from '../services/api';

const DEFAULT_STATION_SLUG = 'toc-s1';
const BASE_STATION_POSITION: LatLngExpression = [18.4663, -66.1057];

const ADSB_EVENT_COLOR = '#1f77b4';
const GENERIC_EVENT_COLOR = '#ff7f0e';

const formatTimestamp = (value: string | undefined) => {
  if (!value) {
    return 'Unknown time';
  }

  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    console.warn('Failed to format timestamp', error);
    return value;
  }
};

const fallBackEvents = [
  {
    id: 1,
    source_id: 101,
    latitude: 18.5,
    longitude: -66.1,
    event_time: new Date().toISOString(),
    received_at: new Date().toISOString(),
    payload: { callsign: 'TEST123' },
    status: 'succeeded',
    station_id: 1,
    source: {
      id: 101,
      name: 'Fallback ADS-B',
      slug: 'fallback-adsb',
      source_type: 'adsb',
      description: 'Fallback ADS-B contact',
      station_id: 1,
    },
  },
];

const fallBackStation = {
  id: 0,
  slug: DEFAULT_STATION_SLUG,
  name: 'TOC-S1',
  description: 'Fallback TOC station overview',
  timezone: 'UTC',
};

const MapPage = () => {
  const [showAdsbOverlay, setShowAdsbOverlay] = useState(true);
  const { data: dashboard } = useStationDashboard(DEFAULT_STATION_SLUG);
  const { data: telemetryEvents } = useTelemetryEvents(DEFAULT_STATION_SLUG);

  const events = telemetryEvents && telemetryEvents.length > 0 ? telemetryEvents : fallBackEvents;
  const station = dashboard?.station ?? fallBackStation;

  const connectorStatuses = useMemo(() => {
    const now = Date.now();
    const grouped = new Map<string, { name: string; lastSeen?: number }>();

    events.forEach((event) => {
      const sourceType = event.source.source_type || 'unknown';
      const key = sourceType.toLowerCase();
      const lastSeen = new Date(event.event_time ?? event.received_at).getTime();
      const existing = grouped.get(key);

      if (!existing || (existing.lastSeen ?? 0) < lastSeen) {
        grouped.set(key, {
          name: event.source.name,
          lastSeen,
        });
      }
    });

    return Array.from(grouped.entries()).map(([key, value]) => {
      const minutesSince = value.lastSeen ? (now - value.lastSeen) / 60000 : Number.POSITIVE_INFINITY;
      let status: 'online' | 'stale' | 'offline' = 'offline';

      if (minutesSince <= 5) {
        status = 'online';
      } else if (minutesSince <= 60) {
        status = 'stale';
      }

      return {
        id: key,
        label: value.name,
        status,
        lastSeen: value.lastSeen,
      };
    });
  }, [events]);

  const adsbEvents = useMemo(() => events.filter((event) => event.source.source_type === 'adsb'), [events]);
  const otherEvents = useMemo(
    () => events.filter((event) => event.source.source_type !== 'adsb'),
    [events],
  );

  return (
    <section className="map-dashboard">
      <header className="map-dashboard__header">
        <div>
          <h2>{station.name} Operational Map</h2>
          <p className="map-dashboard__subtitle">Monitor telemetry overlays and connector health.</p>
        </div>
        <div className="map-dashboard__toggles">
          <label className="toggle">
            <input
              type="checkbox"
              checked={showAdsbOverlay}
              onChange={(event) => setShowAdsbOverlay(event.target.checked)}
            />
            <span>ADS-B overlay</span>
          </label>
          <span data-testid="adsb-track-count">ADS-B tracks: {showAdsbOverlay ? adsbEvents.length : 0}</span>
        </div>
      </header>
      <div className="map-dashboard__body">
        <MapContainer center={BASE_STATION_POSITION} zoom={8} scrollWheelZoom className="map-dashboard__map">
          <TileLayer
            url={import.meta.env.VITE_MAP_TILES_URL}
            attribution={import.meta.env.VITE_MAP_ATTRIBUTION}
          />
          <Marker position={BASE_STATION_POSITION} data-testid="base-station-marker">
            <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent>
              Base Station
            </Tooltip>
          </Marker>
          {showAdsbOverlay && (
            <LayerGroup>
              {adsbEvents.map((event) => (
                <CircleMarker
                  center={[event.latitude ?? BASE_STATION_POSITION[0], event.longitude ?? BASE_STATION_POSITION[1]]}
                  radius={8}
                  pathOptions={{ color: ADSB_EVENT_COLOR, fillOpacity: 0.6 }}
                  key={`adsb-${event.id}`}
                  data-testid="adsb-marker"
                >
                  <Tooltip direction="top">
                    <strong>{event.source.name}</strong>
                    <div>{formatTimestamp(event.event_time ?? event.received_at)}</div>
                  </Tooltip>
                </CircleMarker>
              ))}
            </LayerGroup>
          )}
          <LayerGroup>
            {otherEvents.map((event) => (
              <CircleMarker
                center={[event.latitude ?? BASE_STATION_POSITION[0], event.longitude ?? BASE_STATION_POSITION[1]]}
                radius={6}
                pathOptions={{ color: GENERIC_EVENT_COLOR, fillOpacity: 0.5 }}
                key={`event-${event.id}`}
                data-testid="telemetry-marker"
              >
                <Tooltip direction="top">
                  <strong>{event.source.name}</strong>
                  <div>{formatTimestamp(event.event_time ?? event.received_at)}</div>
                </Tooltip>
              </CircleMarker>
            ))}
          </LayerGroup>
        </MapContainer>
        <aside className="map-dashboard__sidebar">
          <h3>Connector Status</h3>
          <ul>
            {connectorStatuses.length === 0 && <li>No connector data available.</li>}
            {connectorStatuses.map((connector) => (
              <li key={connector.id} data-testid={`connector-${connector.id}`}>
                <span className={`status-indicator status-indicator--${connector.status}`} />
                <div className="status-details">
                  <strong>{connector.label}</strong>
                  <div className="status-meta">
                    {connector.status === 'online' && 'Live telemetry'}
                    {connector.status === 'stale' && 'Telemetry stale'}
                    {connector.status === 'offline' && 'No recent telemetry'}
                  </div>
                  {connector.lastSeen && (
                    <small>Last seen {formatTimestamp(new Date(connector.lastSeen).toISOString())}</small>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </section>
  );
};

export default MapPage;
