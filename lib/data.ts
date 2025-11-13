import fs from 'fs/promises';
import path from 'path';
import { StationDashboard, TimelineEntry } from './types';

export async function loadDashboard(slug: string): Promise<StationDashboard> {
  const p = path.join(process.cwd(), 'public', 'data', `${slug}-dashboard.json`);
  return JSON.parse(await fs.readFile(p, 'utf8'));
}

export async function loadTimeline(slug: string): Promise<TimelineEntry[]> {
  const p = path.join(process.cwd(), 'public', 'data', `${slug}-timeline.json`);
  const arr: TimelineEntry[] = JSON.parse(await fs.readFile(p, 'utf8'));
  // ensure newest first
  return arr.sort((a, b) => +new Date(b.occurred_at) - +new Date(a.occurred_at));
}

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
