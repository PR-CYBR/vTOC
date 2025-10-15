import { useMemo, useState } from 'react';
import { Outlet, Route, Routes, useOutletContext } from 'react-router-dom';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import L, { type LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';

import ChatKitWidget from '../components/chatkit/ChatKitWidget';
import { useTelemetryEvents, type TelemetryEvent } from '../services/api';

const DEFAULT_POSITION: LatLngExpression = [18.4663, -66.1057];

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export interface LayoutContextValue {
  events: TelemetryEvent[];
  isLoading: boolean;
}

const AppLayout = () => {
  const [panelOpen, setPanelOpen] = useState(true);
  const [assistantOpen, setAssistantOpen] = useState(true);
  const { data: events = [], isLoading } = useTelemetryEvents();

  const lastEventTimestamp = useMemo(() => {
    if (!events.length) {
      return undefined;
    }
    const mostRecent = events
      .map((event) => new Date(event.event_time ?? event.received_at).getTime())
      .sort((a, b) => b - a)[0];
    return new Date(mostRecent).toISOString();
  }, [events]);

  const telemetryContext = useMemo(
    () => ({
      events,
      lastEventTimestamp,
      defaultStation: import.meta.env.VITE_AGENTKIT_DEFAULT_STATION_CONTEXT ?? 'PR-SJU',
    }),
    [events, lastEventTimestamp],
  );

  return (
    <div className="app">
      <aside className={`intel-panel ${panelOpen ? 'open' : 'closed'}`}>
        <header>
          <h1>vTOC Intel Feed</h1>
          <div className="panel-actions">
            <button onClick={() => setAssistantOpen((value) => !value)}>
              {assistantOpen ? 'Hide Co-Pilot' : 'Show Co-Pilot'}
            </button>
            <button onClick={() => setPanelOpen((value) => !value)}>
              {panelOpen ? 'Hide' : 'Show'} Intel
            </button>
          </div>
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
        <ChatKitWidget
          open={assistantOpen}
          telemetry={telemetryContext}
          className="chatkit-assistant"
        />
      </aside>
      <main className="map-container">
        <Outlet context={{ events, isLoading }} />
      </main>
    </div>
  );
};

const DashboardRoute = () => {
  const { events, isLoading } = useOutletContext<LayoutContextValue>();

  const markers = useMemo(() => {
    return events.filter((event) => event.latitude && event.longitude);
  }, [events]);

  return (
    <>
      {isLoading && <p className="sr-only">Map is syncing telemetry…</p>}
      <MapContainer center={DEFAULT_POSITION} zoom={8} scrollWheelZoom>
        <TileLayer
          url={import.meta.env.VITE_MAP_TILES_URL}
          attribution={import.meta.env.VITE_MAP_ATTRIBUTION}
        />
        {markers.map((event) => (
          <Marker key={event.id} position={[event.latitude!, event.longitude!] as LatLngExpression}>
            <Popup>
              <strong>{event.source.name}</strong>
              <div>{new Date(event.event_time ?? event.received_at).toLocaleString()}</div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </>
  );
};

const App = () => (
  <Routes>
    <Route element={<AppLayout />}>
      <Route index element={<DashboardRoute />} />
    </Route>
  </Routes>
);

export default App;
