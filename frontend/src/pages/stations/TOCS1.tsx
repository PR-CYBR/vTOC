import { useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L, { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { useStationDashboard, useTelemetryEvents } from '../../services/api';

const STATION_SLUG = 'toc-s1';
const DEFAULT_POSITION: LatLngExpression = [18.4663, -66.1057];

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const TOCS1Dashboard = () => {
  const [panelOpen, setPanelOpen] = useState(true);
  const { data: dashboard } = useStationDashboard(STATION_SLUG);
  const { data: events = [], isLoading } = useTelemetryEvents(STATION_SLUG);

  const markers = useMemo(() => {
    return events.filter((event) => event.latitude && event.longitude);
  }, [events]);

  return (
    <div className="station-dashboard station-dashboard--map">
      <aside className={`intel-panel ${panelOpen ? 'open' : 'closed'}`}>
        <header>
          <div>
            <h2>{dashboard?.station.name ?? 'TOC-S1'}</h2>
            <p className="intel-subtitle">Forward deployed coastal operations</p>
          </div>
          <button onClick={() => setPanelOpen((value) => !value)}>
            {panelOpen ? 'Hide' : 'Show'} Intel
          </button>
        </header>
        <div className="intel-body">
          <div className="kpi-grid">
            <div className="kpi">
              <span className="kpi-label">Events</span>
              <span className="kpi-value">{dashboard?.metrics.total_events ?? 0}</span>
            </div>
            <div className="kpi">
              <span className="kpi-label">Active sources</span>
              <span className="kpi-value">{dashboard?.metrics.active_sources ?? 0}</span>
            </div>
          </div>
          {dashboard?.metrics.last_event && (
            <div className="intel-highlight">
              <h3>Latest Signal</h3>
              <p>{new Date(dashboard.metrics.last_event.event_time ?? dashboard.metrics.last_event.received_at).toLocaleString()}</p>
              <pre>{JSON.stringify(dashboard.metrics.last_event.payload ?? {}, null, 2)}</pre>
            </div>
          )}
          {isLoading && <p>Loading telemetry…</p>}
          {!isLoading && events.length === 0 && <p>No telemetry events available.</p>}
          <ul>
            {events.map((event) => (
              <li key={event.id}>
                <h3>{event.source.name}</h3>
                <p>{new Date(event.event_time ?? event.received_at).toLocaleString()}</p>
                <pre>{JSON.stringify(event.payload ?? {}, null, 2)}</pre>
              </li>
            ))}
          </ul>
        </div>
      </aside>
      <section className="map-container">
        <MapContainer center={DEFAULT_POSITION} zoom={8} scrollWheelZoom>
          <TileLayer
            url={import.meta.env.VITE_MAP_TILES_URL}
            attribution={import.meta.env.VITE_MAP_ATTRIBUTION}
          />
          {markers.map((event) => (
            <Marker key={event.id} position={[event.latitude!, event.longitude!]}
            >
              <Popup>
                <strong>{event.source.name}</strong>
                <div>{new Date(event.event_time ?? event.received_at).toLocaleString()}</div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </section>
    </div>
  );
};

export default TOCS1Dashboard;
