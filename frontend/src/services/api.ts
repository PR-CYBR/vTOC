import axios from 'axios';
import { useQuery } from '@tanstack/react-query';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080'
});

export interface TelemetrySource {
  id: number;
  name: string;
  slug: string;
  source_type: string;
  description?: string;
}

export interface TelemetryEvent {
  id: number;
  source_id: number;
  latitude?: number;
  longitude?: number;
  event_time?: string;
  received_at: string;
  payload?: Record<string, unknown>;
  source: TelemetrySource;
}

export const useTelemetryEvents = () =>
  useQuery<TelemetryEvent[]>({
    queryKey: ['telemetry-events'],
    queryFn: async () => {
      const response = await api.get('/api/v1/telemetry/events');
      return response.data;
    },
    refetchInterval: 60_000,
  });

export default api;
