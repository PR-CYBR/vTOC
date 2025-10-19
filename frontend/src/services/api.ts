import axios from 'axios';
import { useEffect } from 'react';
import {
  QueryKey,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { createClient, type Session, type SupabaseClient } from '@supabase/supabase-js';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
});

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabaseTelemetryTable = import.meta.env.VITE_SUPABASE_TELEMETRY_TABLE ?? 'telemetry_events';

const supabaseClient: SupabaseClient | null =
  supabaseUrl && supabaseAnonKey
    ? createClient(supabaseUrl, supabaseAnonKey, {
        auth: {
          persistSession: true,
          detectSessionInUrl: true,
          autoRefreshToken: true,
        },
      })
    : null;

export type { Session };

export const supabase = supabaseClient;
export const isSupabaseConfigured = Boolean(supabaseClient);

const toNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim().length > 0) {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
};

const normalizeStationRow = (row: Record<string, unknown>): Station => {
  const id = toNumber(row.id) ?? toNumber(row['station_id']) ?? 0;
  const slug = String(row['slug'] ?? row['station_slug'] ?? '');
  return {
    id,
    slug,
    name: String(row['name'] ?? row['station_name'] ?? slug),
    description: (row['description'] as string | undefined) ?? undefined,
    timezone: String(row['timezone'] ?? row['default_timezone'] ?? 'UTC'),
    telemetry_schema: (row['telemetry_schema'] as string | undefined) ?? undefined,
  };
};

const normalizeTelemetryRow = (row: Record<string, any>): TelemetryEvent => {
  const sourceRecord = (row['source'] ?? {}) as Record<string, any>;

  const source: TelemetrySource = {
    id:
      toNumber(sourceRecord['id']) ??
      toNumber(row['source_id']) ??
      0,
    name:
      (sourceRecord['name'] as string | undefined) ??
      (row['source_name'] as string | undefined) ??
      `source-${row['source_id'] ?? 'unknown'}`,
    slug:
      (sourceRecord['slug'] as string | undefined) ??
      (row['source_slug'] as string | undefined) ??
      String(row['source_id'] ?? ''),
    source_type:
      (sourceRecord['source_type'] as string | undefined) ??
      (row['source_type'] as string | undefined) ??
      'unknown',
    description:
      (sourceRecord['description'] as string | undefined) ??
      (row['source_description'] as string | undefined) ??
      undefined,
    station_id:
      toNumber(sourceRecord['station_id']) ??
      toNumber(row['station_id']) ??
      undefined,
  };

  const receivedAt =
    (row['received_at'] as string | undefined) ??
    (row['event_time'] as string | undefined) ??
    new Date().toISOString();

  return {
    id: toNumber(row['id']) ?? 0,
    source_id: toNumber(row['source_id']) ?? 0,
    latitude: toNumber(row['latitude']),
    longitude: toNumber(row['longitude']),
    event_time: (row['event_time'] as string | undefined) ?? undefined,
    received_at: receivedAt,
    payload: (row['payload'] as Record<string, unknown> | undefined) ?? undefined,
    status: (row['status'] as string | undefined) ?? 'unprocessed',
    station_id: toNumber(row['station_id']) ?? undefined,
    source,
  };
};

const fetchStationsFromSupabase = async (): Promise<Station[]> => {
  if (!supabaseClient) {
    throw new Error('Supabase client is not configured');
  }

  const { data, error } = await supabaseClient
    .from('stations')
    .select('*')
    .order('name', { ascending: true });

  if (error) {
    throw error;
  }

  return (data ?? []).map((row) => normalizeStationRow(row as Record<string, unknown>));
};

const fetchTelemetryFromSupabase = async (
  stationSlug?: string,
): Promise<TelemetryEvent[]> => {
  if (!supabaseClient) {
    throw new Error('Supabase client is not configured');
  }

  let query = supabaseClient
    .from(supabaseTelemetryTable)
    .select('*')
    .order('event_time', { ascending: false })
    .limit(100);

  if (stationSlug) {
    query = query.eq('station_slug', stationSlug);
  }

  const { data, error } = await query;

  if (error) {
    throw error;
  }

  return (data ?? []).map((row) => normalizeTelemetryRow(row as Record<string, any>));
};

const subscribeToSupabaseTable = ({
  queryClient,
  queryKey,
  table,
  filter,
}: {
  queryClient: ReturnType<typeof useQueryClient>;
  queryKey: QueryKey;
  table: string;
  filter?: string;
}) => {
  if (!supabaseClient) {
    return () => undefined;
  }

  const channelName = `public:${table}:${filter ?? 'all'}`;
  const channel = supabaseClient
    .channel(channelName)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table,
        ...(filter ? { filter } : {}),
      },
      () => {
        queryClient.invalidateQueries({ queryKey });
      },
    );

  channel.subscribe((status) => {
    if (status === 'CHANNEL_ERROR') {
      console.error(`Supabase channel error for ${channelName}`);
    }
  });

  return () => {
    supabaseClient.removeChannel(channel);
  };
};

export interface Station {
  id: number;
  slug: string;
  name: string;
  description?: string;
  timezone: string;
  telemetry_schema?: string;
}

export interface TelemetrySource {
  id: number;
  name: string;
  slug: string;
  source_type: string;
  description?: string;
  station_id?: number;
}

export interface TelemetryEvent {
  id: number;
  source_id: number;
  latitude?: number;
  longitude?: number;
  event_time?: string;
  received_at: string;
  payload?: Record<string, unknown>;
  status: string;
  station_id?: number;
  source: TelemetrySource;
}

export interface StationDashboardMetrics {
  total_events: number;
  active_sources: number;
  last_event?: TelemetryEvent;
}

export interface StationDashboard {
  station: Station;
  metrics: StationDashboardMetrics;
}

export interface StationTask {
  id: string;
  title: string;
  status: string;
  priority: string;
  created_at: string;
  due_at?: string;
  metadata: Record<string, unknown>;
}

export interface StationTaskQueue {
  station: Station;
  tasks: StationTask[];
}

export interface AgentAction {
  name: string;
  description: string;
  endpoint: string;
  method: string;
  metadata: Record<string, unknown>;
}

export interface StationAgentCatalog {
  station: Station;
  actions: AgentAction[];
}

export type StationTimelineEventType =
  | 'telemetry'
  | 'task'
  | 'incident'
  | 'agent'
  | 'communication'
  | string;

export interface StationTimelineEntry {
  id: string;
  type: StationTimelineEventType;
  occurred_at: string;
  title: string;
  summary?: string;
  source?: string;
  icon: string;
  payload?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  raw: Record<string, unknown>;
}

const stationHeaders = (stationSlug?: string) =>
  stationSlug
    ? {
        headers: {
          'X-Station-Id': stationSlug,
        },
      }
    : {};

const TIMELINE_ICON_MAP: Record<string, string> = {
  telemetry: '📡',
  task: '📝',
  incident: '⚠️',
  agent: '🤖',
  communication: '💬',
  default: '🛰️',
};

const toStringSafe = (value: unknown): string | undefined => {
  if (typeof value === 'string') {
    return value;
  }

  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toString();
  }

  return undefined;
};

const toISODate = (value: unknown): string | undefined => {
  if (typeof value === 'string') {
    const date = new Date(value);
    if (!Number.isNaN(date.getTime())) {
      return date.toISOString();
    }
  }

  if (typeof value === 'number' && Number.isFinite(value)) {
    const date = new Date(value);
    if (!Number.isNaN(date.getTime())) {
      return date.toISOString();
    }
  }

  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return value.toISOString();
  }

  return undefined;
};

const toRecord = (value: unknown): Record<string, unknown> | undefined => {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }

  return undefined;
};

const stableTimelineId = (value: Record<string, unknown>): string => {
  const candidates = [
    toStringSafe(value['id']),
    toStringSafe(value['uuid']),
    toStringSafe(value['event_id']),
    toStringSafe(value['timeline_id']),
    toStringSafe(value['reference']),
  ];

  const explicit = candidates.find((candidate) => candidate && candidate.trim().length > 0);
  if (explicit) {
    return explicit;
  }

  const type = toStringSafe(value['type']) ?? toStringSafe(value['event_type']) ?? 'event';
  const timestamp =
    toStringSafe(value['occurred_at']) ??
    toStringSafe(value['timestamp']) ??
    toStringSafe(value['event_time']) ??
    toStringSafe(value['created_at']) ??
    toStringSafe(value['received_at']) ??
    'unknown';

  const fingerprint = `${type}-${timestamp}`;

  let hash = 0;
  for (let index = 0; index < fingerprint.length; index += 1) {
    const charCode = fingerprint.charCodeAt(index);
    hash = (hash << 5) - hash + charCode;
    hash |= 0;
  }

  return `timeline-${Math.abs(hash)}`;
};

const normalizeTimelinePayload = (
  value: unknown,
): Record<string, unknown> | undefined => {
  const record = toRecord(value);
  if (record) {
    return record;
  }

  return undefined;
};

const pickTimelineIcon = (type: string | undefined): string => {
  if (!type) {
    return TIMELINE_ICON_MAP.default;
  }

  const normalized = type.toLowerCase();

  if (TIMELINE_ICON_MAP[normalized]) {
    return TIMELINE_ICON_MAP[normalized];
  }

  const baseType = normalized.split('.')[0];
  if (TIMELINE_ICON_MAP[baseType]) {
    return TIMELINE_ICON_MAP[baseType];
  }

  return TIMELINE_ICON_MAP.default;
};

const normalizeStationTimelineEntry = (
  value: Record<string, unknown>,
): StationTimelineEntry => {
  const type =
    (toStringSafe(value['type']) ??
      toStringSafe(value['event_type']) ??
      toStringSafe(value['kind']) ??
      'event') as StationTimelineEventType;

  const occurredAt =
    toISODate(value['occurred_at']) ??
    toISODate(value['timestamp']) ??
    toISODate(value['event_time']) ??
    toISODate(value['created_at']) ??
    toISODate(value['received_at']) ??
    new Date().toISOString();

  const sourceRecord = toRecord(value['source']);
  const metadataRecord =
    normalizeTimelinePayload(value['metadata']) ??
    normalizeTimelinePayload(value['context']) ??
    undefined;

  const payloadRecord =
    normalizeTimelinePayload(value['payload']) ??
    normalizeTimelinePayload(value['data']) ??
    normalizeTimelinePayload(value['details']) ??
    undefined;

  const summaryCandidate =
    toStringSafe(value['summary']) ??
    toStringSafe(value['description']) ??
    toStringSafe(value['status']);

  const titleCandidate =
    toStringSafe(value['title']) ??
    toStringSafe(value['name']) ??
    (sourceRecord ? toStringSafe(sourceRecord['name']) : undefined) ??
    type;

  const sourceName =
    (sourceRecord ? toStringSafe(sourceRecord['name']) : undefined) ??
    toStringSafe(value['source']);

  return {
    id: stableTimelineId(value),
    type,
    occurred_at: occurredAt,
    title: titleCandidate ?? type,
    summary: summaryCandidate ?? undefined,
    source: sourceName ?? undefined,
    icon: pickTimelineIcon(type),
    payload: payloadRecord,
    metadata: metadataRecord,
    raw: value,
  };
};

const unwrapTimelineResponse = (
  payload: unknown,
): Record<string, unknown>[] => {
  if (Array.isArray(payload)) {
    return payload as Record<string, unknown>[];
  }

  if (payload && typeof payload === 'object') {
    const candidate = payload as Record<string, unknown>;
    const entries = candidate['entries'] ?? candidate['timeline'] ?? candidate['items'];
    if (Array.isArray(entries)) {
      return entries as Record<string, unknown>[];
    }
  }

  return [];
};

export const normalizeStationTimeline = (
  entries: Record<string, unknown>[],
): StationTimelineEntry[] =>
  entries
    .map((entry) => normalizeStationTimelineEntry(entry))
    .sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime());

export const useSupabaseSession = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!supabaseClient) {
      return;
    }

    const { data: listener } = supabaseClient.auth.onAuthStateChange((_, session) => {
      queryClient.setQueryData(['supabase-session'], session ?? null);
    });

    return () => {
      listener.subscription.unsubscribe();
    };
  }, [queryClient]);

  return useQuery<Session | null>({
    queryKey: ['supabase-session'],
    enabled: Boolean(supabaseClient),
    queryFn: async () => {
      if (!supabaseClient) {
        return null;
      }
      const { data } = await supabaseClient.auth.getSession();
      return data.session ?? null;
    },
    staleTime: 5 * 60 * 1000,
  });
};

export const useStations = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!supabaseClient) {
      return;
    }

    return subscribeToSupabaseTable({
      queryClient,
      queryKey: ['stations'],
      table: 'stations',
    });
  }, [queryClient]);

  return useQuery<Station[]>({
    queryKey: ['stations'],
    queryFn: async () => {
      if (supabaseClient) {
        try {
          return await fetchStationsFromSupabase();
        } catch (error) {
          console.warn('Falling back to API for station list', error);
        }
      }

      const response = await api.get('/api/v1/stations/');
      return response.data;
    },
  });
};

export const useTelemetryEvents = (stationSlug?: string) => {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!supabaseClient) {
      return;
    }

    return subscribeToSupabaseTable({
      queryClient,
      queryKey: ['telemetry-events', stationSlug ?? 'default'],
      table: supabaseTelemetryTable,
      filter: stationSlug ? `station_slug=eq.${stationSlug}` : undefined,
    });
  }, [queryClient, stationSlug]);

  return useQuery<TelemetryEvent[]>({
    queryKey: ['telemetry-events', stationSlug ?? 'default'],
    queryFn: async () => {
      if (supabaseClient) {
        try {
          return await fetchTelemetryFromSupabase(stationSlug);
        } catch (error) {
          console.warn('Falling back to API for telemetry events', error);
        }
      }

      const response = await api.get('/api/v1/telemetry/events', {
        ...stationHeaders(stationSlug),
      });
      return response.data;
    },
    refetchInterval: supabaseClient ? false : 60_000,
  });
};

export const useStationDashboard = (stationSlug: string) =>
  useQuery<StationDashboard>({
    queryKey: ['station-dashboard', stationSlug],
    queryFn: async () => {
      const response = await api.get(`/api/v1/stations/${stationSlug}/dashboard`);
      return response.data;
    },
  });

export const useStationTasks = (stationSlug: string) =>
  useQuery<StationTaskQueue>({
    queryKey: ['station-tasks', stationSlug],
    queryFn: async () => {
      const response = await api.get(`/api/v1/stations/${stationSlug}/tasks`);
      return response.data;
    },
  });

export const useStationAgentActions = (stationSlug: string) =>
  useQuery<StationAgentCatalog>({
    queryKey: ['station-agentkit', stationSlug],
    queryFn: async () => {
      const response = await api.get(`/api/v1/stations/${stationSlug}/agentkit/actions`);
      return response.data;
    },
  });

const fetchStationTimeline = async (stationSlug: string): Promise<StationTimelineEntry[]> => {
  const response = await api.get(`/api/v1/stations/${stationSlug}/timeline`);
  const rawEntries = unwrapTimelineResponse(response.data);
  return normalizeStationTimeline(rawEntries);
};

export const useStationTimeline = (stationSlug: string) =>
  useQuery<StationTimelineEntry[]>({
    queryKey: ['station-timeline', stationSlug],
    queryFn: () => fetchStationTimeline(stationSlug),
    staleTime: 30_000,
  });

export default api;
