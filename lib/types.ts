export type StationDashboard = {
  station: { name: string; role: string; callsign?: string };
  metrics: { total_events: number; active_sources: number; last_event?: TimelineEntry };
};

export type TimelineEntry = {
  id: number | string;
  occurred_at: string;         // ISO
  type: string;
  title: string;
  source?: string;
  summary?: string;
  payload?: unknown;
  icon?: string;               // optional emoji/icon
};

// Map types
export type BaseMapType = 'streets' | 'satellite';
export type OverlayType = 'sensor-ranges' | 'heatmap';

export interface GeoJSONFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  properties?: Record<string, unknown>;
}

export interface GeoJSONData {
  type: string;
  features: GeoJSONFeature[];
}

// Mission Console types
export interface TelemetrySubmission {
  message: string;
  timestamp: string;
}

export interface AgentTrigger {
  command: string;
  timestamp: string;
}
