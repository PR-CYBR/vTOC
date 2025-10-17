import '@testing-library/jest-dom/vitest';

import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockEvents = [
  {
    id: 1,
    source_id: 101,
    latitude: 18.55,
    longitude: -66.12,
    event_time: new Date().toISOString(),
    received_at: new Date().toISOString(),
    status: 'succeeded',
    station_id: 1,
    payload: {},
    source: {
      id: 101,
      name: 'ADS-B Feed',
      slug: 'adsb-feed',
      source_type: 'adsb',
      description: 'ADS-B overlay',
      station_id: 1,
    },
  },
  {
    id: 2,
    source_id: 102,
    latitude: 18.52,
    longitude: -66.18,
    event_time: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    received_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    status: 'succeeded',
    station_id: 1,
    payload: {},
    source: {
      id: 102,
      name: 'Coastal Radar',
      slug: 'radar',
      source_type: 'radar',
      description: 'Shore based radar',
      station_id: 1,
    },
  },
];

vi.mock('../services/api', () => ({
  useStationDashboard: () => ({
    data: {
      station: {
        id: 1,
        slug: 'toc-s1',
        name: 'Test Station',
        description: 'Mock station',
        timezone: 'UTC',
      },
    },
  }),
  useTelemetryEvents: () => ({
    data: mockEvents,
  }),
}));

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: ReactNode }) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  Marker: ({ children, ...props }: any) => (
    <div data-testid={props['data-testid'] ?? 'marker'}>{children}</div>
  ),
  Tooltip: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  LayerGroup: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CircleMarker: ({ children, ...props }: any) => (
    <div data-testid={props['data-testid']}>{children}</div>
  ),
}));

import MapPage from './Map';

describe('MapPage', () => {
  it('renders base station marker and connector statuses', () => {
    render(<MapPage />);

    expect(screen.getByTestId('base-station-marker')).toBeInTheDocument();
    expect(screen.getByTestId('connector-adsb')).toHaveTextContent(/live telemetry/i);
    expect(screen.getByTestId('connector-radar')).toHaveTextContent(/telemetry stale/i);
  });

  it('toggles ADS-B overlay visibility', async () => {
    const user = userEvent.setup();
    render(<MapPage />);

    expect(screen.getAllByTestId('adsb-marker')).toHaveLength(1);
    expect(screen.getByTestId('adsb-track-count')).toHaveTextContent('ADS-B tracks: 1');
    const toggle = screen.getByLabelText(/ads-b overlay/i);
    await user.click(toggle);
    expect(screen.queryByTestId('adsb-marker')).toBeNull();
    expect(screen.getByTestId('adsb-track-count')).toHaveTextContent('ADS-B tracks: 0');
  });
});
