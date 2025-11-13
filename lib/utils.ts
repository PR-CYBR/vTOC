import { TimelineEntry } from './types';

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
