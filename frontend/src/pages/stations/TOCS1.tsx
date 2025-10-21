import { useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L, { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { useStationDashboard, useTelemetryEvents } from '../../services/api';
import MockTelemetryOverlay from '../../components/telemetry/MockTelemetryOverlay';
import StationTimelinePanel from '../../components/telemetry/StationTimelinePanel';

const STATION_SLUG = 'toc-s1';
const DEFAULT_POSITION: LatLngExpression = [18.4663, -66.1057];
const MAP_TILES_URL =
  import.meta.env.VITE_MAP_TILES_URL ?? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const MAP_ATTRIBUTION =
  import.meta.env.VITE_MAP_ATTRIBUTION ?? '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors';

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const TOCS1Dashboard = () => {
  const [panelOpen, setPanelOpen] = useState(true);
  const [overlayOpen, setOverlayOpen] = useState(false);
  const { data: dashboard } = useStationDashboard(STATION_SLUG);
  const { data: events = [] } = useTelemetryEvents(STATION_SLUG);

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
          <button type="button" onClick={() => setOverlayOpen(true)} className="mock-overlay__trigger">
            Show mock telemetry
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
          <StationTimelinePanel stationSlug={STATION_SLUG} />
        </div>
      </aside>
      <section className="map-container">
        <MapContainer center={DEFAULT_POSITION} zoom={8} scrollWheelZoom>
          <TileLayer
            url={MAP_TILES_URL}
            attribution={MAP_ATTRIBUTION}
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
        <MockTelemetryOverlay open={overlayOpen} events={events} onClose={() => setOverlayOpen(false)} />
      </section>
    </div>
  );
};

export default TOCS1Dashboard;
