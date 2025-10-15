import { Navigate, NavLink, Route, Routes } from 'react-router-dom';

import TOCS1Dashboard from './stations/TOCS1';
import TOCS2Dashboard from './stations/TOCS2';
import TOCS3Dashboard from './stations/TOCS3';
import TOCS4Dashboard from './stations/TOCS4';

const StationNav = () => {
  const items = [
    { path: '/stations/toc-s1', label: 'TOC-S1' },
    { path: '/stations/toc-s2', label: 'TOC-S2' },
    { path: '/stations/toc-s3', label: 'TOC-S3' },
    { path: '/stations/toc-s4', label: 'TOC-S4' }
  ];

  return (
    <nav className="station-nav">
      {items.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) => `station-nav__link${isActive ? ' station-nav__link--active' : ''}`}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
};

const App = () => {
  return (
    <div className="station-shell">
      <header className="station-header">
        <h1>vTOC Station Command</h1>
        <StationNav />
      </header>
      <main className="station-content">
        <Routes>
          <Route path="/" element={<Navigate to="/stations/toc-s1" replace />} />
          <Route path="/stations/toc-s1" element={<TOCS1Dashboard />} />
          <Route path="/stations/toc-s2" element={<TOCS2Dashboard />} />
          <Route path="/stations/toc-s3" element={<TOCS3Dashboard />} />
          <Route path="/stations/toc-s4" element={<TOCS4Dashboard />} />
        </Routes>
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
