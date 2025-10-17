import type { TelemetryEvent } from '../../services/api';

interface MockTelemetryOverlayProps {
  open: boolean;
  events: TelemetryEvent[];
  onClose: () => void;
}

const fallbackTelemetry: TelemetryEvent[] = [
  {
    id: 1,
    source_id: 101,
    latitude: 18.456,
    longitude: -66.105,
    event_time: new Date().toISOString(),
    received_at: new Date().toISOString(),
    payload: { callsign: 'N7823C', altitude_ft: 1250, speed_knots: 145 },
    status: 'mocked',
    station_id: 1,
    source: {
      id: 101,
      name: 'Mock ADS-B feed',
      slug: 'mock-adsb',
      source_type: 'adsb',
      description: 'Synthetic training track',
      station_id: 1,
    },
  },
];

const MockTelemetryOverlay = ({ open, events, onClose }: MockTelemetryOverlayProps) => {
  const data = events.length > 0 ? events : fallbackTelemetry;

  if (!open) {
    return null;
  }

  return (
    <aside className="telemetry-overlay" role="complementary" aria-label="Mock telemetry overlay">
      <header>
        <h3>Mock telemetry overlay</h3>
        <button type="button" onClick={onClose} aria-label="Hide mock telemetry overlay">
          Close
        </button>
      </header>
      <p>Hardware feeds are mocked for end-to-end tests. The overlay renders recent ADS-B and GPS events.</p>
      <ul>
        {data.map((event) => (
          <li key={`${event.source.slug}-${event.id}`}>
            <strong>{event.source.name}</strong>
            <span>
              {event.latitude?.toFixed(3)}, {event.longitude?.toFixed(3)}
            </span>
            <span>
              {typeof event.payload?.callsign === 'string'
                ? event.payload.callsign
                : 'Unknown'}
            </span>
          </li>
        ))}
      </ul>
    </aside>
  );
};

export default MockTelemetryOverlay;
