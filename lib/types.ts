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
