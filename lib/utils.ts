import { TimelineEntry, GeoJSONData } from './types';

export function groupByDate(entries: TimelineEntry[]): Record<string, TimelineEntry[]> {
  return entries.reduce((acc, e) => {
    const key = e.occurred_at.slice(0, 10);
    (acc[key] ||= []).push(e);
    return acc;
  }, {} as Record<string, TimelineEntry[]>);
}

export function payloadExcerpt(payload: unknown, max = 220): string {
  const s = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
  return s.length > max ? s.slice(0, max) + '…' : s;
}

/**
 * Fetches GeoJSON data from a given URL
 */
export async function fetchGeoJSON(url: string): Promise<GeoJSONData> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch GeoJSON: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Validates if the given data is valid GeoJSON
 */
export function isValidGeoJSON(data: unknown): data is GeoJSONData {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;
  return obj.type === 'FeatureCollection' && Array.isArray(obj.features);
}
