import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  useStationTimeline: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    useStationTimeline: mocks.useStationTimeline,
  };
});

const mockUseStationTimeline = mocks.useStationTimeline;

import StationTimelinePanel from './StationTimelinePanel';

describe('StationTimelinePanel', () => {
  beforeEach(() => {
    mockUseStationTimeline.mockReset();
  });

  it('renders grouped entries with payload excerpts and icons', () => {
    mockUseStationTimeline.mockReturnValue({
      data: [
        {
          id: '1',
          type: 'telemetry',
          occurred_at: '2024-01-03T10:00:00Z',
          title: 'Signal received',
          summary: 'Thermal spike detected',
          source: 'Sensor Alpha',
          icon: '📡',
          payload: { temperature: 28.3, unit: 'C' },
          metadata: {},
          raw: {},
        },
        {
          id: '2',
          type: 'task',
          occurred_at: '2024-01-02T18:30:00Z',
          title: 'Task assigned',
          summary: 'Deploy search drone',
          source: 'Mission Control',
          icon: '📝',
          payload: { priority: 'high', assignee: 'Falcon-1' },
          metadata: {},
          raw: {},
        },
      ],
      isLoading: false,
      error: null,
    });

    const { container } = render(<StationTimelinePanel stationSlug="toc-s1" />);

    expect(screen.getByText('Station Timeline')).toBeDefined();
    expect(screen.getByText('Thermal spike detected')).toBeDefined();
    expect(screen.getAllByRole('heading', { level: 4 }).length).toBeGreaterThan(0);
    expect(screen.getByText('telemetry')).toBeDefined();
    const payloads = screen.getAllByLabelText('Event payload excerpt');
    expect(payloads[0].textContent).toContain('temperature');
    expect(payloads[1].textContent).toContain('priority');

    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders a loading state while fetching data', () => {
    mockUseStationTimeline.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    render(<StationTimelinePanel stationSlug="toc-s1" />);

    expect(screen.getByText('Loading timeline…')).toBeDefined();
  });
});
