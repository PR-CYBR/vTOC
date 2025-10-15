import { useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L, { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { useTelemetryEvents } from '../services/api';

const DEFAULT_POSITION: LatLngExpression = [18.4663, -66.1057];

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const App = () => {
  const [panelOpen, setPanelOpen] = useState(true);
  const { data: events = [], isLoading } = useTelemetryEvents();

  const markers = useMemo(() => {
    return events.filter((event) => event.latitude && event.longitude);
  }, [events]);

  return (
    <div className="app">
      <div className={`intel-panel ${panelOpen ? 'open' : 'closed'}`}>
        <header>
          <h1>vTOC Intel Feed</h1>
          <button onClick={() => setPanelOpen((value) => !value)}>
            {panelOpen ? 'Hide' : 'Show'} Intel
          </button>
        </header>
        <div className="intel-body">
          {isLoading && <p>Loading telemetry…</p>}
          {!isLoading && events.length === 0 && <p>No telemetry events available.</p>}
          <ul>
            {events.map((event) => (
              <li key={event.id}>
                <h2>{event.source.name}</h2>
                <p>{new Date(event.event_time ?? event.received_at).toLocaleString()}</p>
                <pre>{JSON.stringify(event.payload ?? {}, null, 2)}</pre>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="map-container">
        <MapContainer center={DEFAULT_POSITION} zoom={8} scrollWheelZoom>
          <TileLayer
            url={import.meta.env.VITE_MAP_TILES_URL}
            attribution={import.meta.env.VITE_MAP_ATTRIBUTION}
          />
          {markers.map((event) => (
            <Marker key={event.id} position={[event.latitude!, event.longitude!]}>
              <Popup>
                <strong>{event.source.name}</strong>
                <div>{new Date(event.event_time ?? event.received_at).toLocaleString()}</div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default App;
