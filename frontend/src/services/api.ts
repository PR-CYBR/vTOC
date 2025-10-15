import axios from 'axios';
import { useQuery } from '@tanstack/react-query';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080'
});

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

const stationHeaders = (stationSlug?: string) =>
  stationSlug
    ? {
        headers: {
          'X-Station-Id': stationSlug
        }
      }
    : {};

export const useStations = () =>
  useQuery<Station[]>({
    queryKey: ['stations'],
    queryFn: async () => {
      const response = await api.get('/api/v1/stations/');
      return response.data;
    },
  });

export const useTelemetryEvents = (stationSlug?: string) =>
  useQuery<TelemetryEvent[]>({
    queryKey: ['telemetry-events', stationSlug ?? 'default'],
    queryFn: async () => {
      const response = await api.get('/api/v1/telemetry/events', {
        ...stationHeaders(stationSlug)
      });
      return response.data;
    },
    refetchInterval: 60_000,
  });

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

export default api;
