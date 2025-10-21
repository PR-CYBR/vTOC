import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

import api, {
  normalizeStationTimeline,
  type StationTimelineEntry,
  useStationTimeline,
} from '../services/api';

const buildWrapper = (children: ReactNode, queryClient: QueryClient) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const TimelineConsumer = ({ stationSlug }: { stationSlug: string }) => {
  const { data, isLoading } = useStationTimeline(stationSlug);

  if (isLoading) {
    return <span>Loading…</span>;
  }

  return <output data-testid="timeline-count">{data?.length ?? 0}</output>;
};

describe('station timeline helpers', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('normalizes mixed timeline event shapes into a consistent payload', () => {
    const raw: Record<string, unknown>[] = [
      {
        id: 42,
        type: 'telemetry',
        event_time: '2024-01-02T10:00:00Z',
        payload: { temperature: 21.4 },
        source: { name: 'Sensor Alpha' },
      },
      {
        uuid: 'task-7',
        kind: 'task',
        created_at: '2024-01-01T22:00:00Z',
        title: 'Re-task drone',
        description: 'Shift ISR orbit to sector 4',
        metadata: { priority: 'high' },
      },
      {
        reference: 'incident-3',
        event_type: 'incident',
        timestamp: 1704211200000,
        summary: 'Weather warning triggered',
        details: { severity: 'medium' },
      },
    ];

    const normalized = normalizeStationTimeline(raw);

    expect(normalized).toHaveLength(3);

    const telemetry = normalized.find((entry) => entry.type === 'telemetry');
    const incident = normalized.find((entry) => entry.type === 'incident');
    const task = normalized.find((entry) => entry.type === 'task');

    expect(telemetry?.occurred_at).toBe('2024-01-02T10:00:00.000Z');
    expect(telemetry?.icon).toBe('📡');
    expect(incident?.icon).toBe('⚠️');
    expect(task?.metadata).toEqual({ priority: 'high' });
    expect(task?.payload).toBeUndefined();
  });

  it('fetches timeline data via React Query and caches normalized results', async () => {
    const responsePayload = {
      entries: [
        { id: 'a', type: 'agent', occurred_at: '2024-01-03T12:00:00Z' },
        { id: 'b', type: 'communication', occurred_at: '2024-01-02T12:00:00Z' },
      ],
    };

    const getSpy = vi
      .spyOn(api, 'get')
      .mockResolvedValue({ data: responsePayload } as any);

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(buildWrapper(<TimelineConsumer stationSlug="toc-s1" />, queryClient));

    await waitFor(() => {
      expect(screen.getByTestId('timeline-count').textContent).toBe('2');
    });

    const cached = queryClient.getQueryData<StationTimelineEntry[]>([
      'station-timeline',
      'toc-s1',
    ]);

    expect(cached).toBeDefined();
    expect(cached?.[0].id).toBe('a');
    expect(cached?.[0].icon).toBe('🤖');
    expect(cached?.[1].icon).toBe('💬');
    expect(getSpy).toHaveBeenCalledWith('/api/v1/stations/toc-s1/timeline');
  });
});
