import { useMemo, type ReactNode } from 'react';

import {
  type StationTimelineEntry,
  useStationTimeline,
} from '../../services/api';

interface StationTimelinePanelProps {
  stationSlug: string;
  className?: string;
  limit?: number;
  emptyState?: ReactNode;
}

interface TimelineGroup {
  key: string;
  label: string;
  entries: StationTimelineEntry[];
}

const sanitizeTypeForClassName = (type: string) =>
  (type
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')) || 'event';

const formatGroupLabel = (isoDate: string): string => {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) {
    return isoDate;
  }

  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

const formatTimeLabel = (isoDate: string): string => {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) {
    return isoDate;
  }

  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });
};

const buildPayloadExcerpt = (payload?: Record<string, unknown>): string | undefined => {
  if (!payload || Object.keys(payload).length === 0) {
    return undefined;
  }

  try {
    const serialized = JSON.stringify(payload, null, 2);
    if (!serialized) {
      return undefined;
    }

    const trimmed = serialized.trim();
    if (trimmed.length <= 220) {
      return trimmed;
    }

    return `${trimmed.slice(0, 217)}…`;
  } catch (error) {
    console.warn('Unable to serialize timeline payload', error);
    return undefined;
  }
};

const groupTimelineEntries = (entries: StationTimelineEntry[]): TimelineGroup[] => {
  const groups = new Map<string, TimelineGroup>();

  entries.forEach((entry) => {
    const key = entry.occurred_at.slice(0, 10);
    const label = formatGroupLabel(entry.occurred_at);
    const existing = groups.get(key);

    if (existing) {
      existing.entries.push(entry);
    } else {
      groups.set(key, {
        key,
        label,
        entries: [entry],
      });
    }
  });

  return Array.from(groups.values())
    .sort((a, b) => new Date(b.key).getTime() - new Date(a.key).getTime())
    .map((group) => ({
      ...group,
      entries: [...group.entries].sort(
        (a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime(),
      ),
    }));
};

const StationTimelinePanel = ({
  stationSlug,
  className,
  limit,
  emptyState,
}: StationTimelinePanelProps) => {
  const { data, isLoading, error } = useStationTimeline(stationSlug);

  const entries = useMemo(() => {
    const list = data ?? [];
    return typeof limit === 'number' ? list.slice(0, limit) : list;
  }, [data, limit]);

  const groups = useMemo(() => groupTimelineEntries(entries), [entries]);

  const panelClassName = ['station-timeline-panel', className]
    .filter(Boolean)
    .join(' ');

  const errorMessage = error instanceof Error ? error.message : undefined;

  return (
    <section className={panelClassName} aria-label="Station timeline">
      <header className="station-timeline-panel__header">
        <div>
          <h3>Station Timeline</h3>
          <p className="station-timeline-panel__subtitle">
            Unified view of telemetry, tasks, agent actions, and alerts
          </p>
        </div>
        <span className="station-timeline-panel__count" aria-label="Timeline entry count">
          {data?.length ?? 0}
        </span>
      </header>
      <div className="station-timeline-panel__body">
        {isLoading && <p className="station-timeline-panel__status">Loading timeline…</p>}
        {!isLoading && error && (
          <p className="station-timeline-panel__status station-timeline-panel__status--error" role="alert">
            Unable to load timeline{errorMessage ? `: ${errorMessage}` : '.'}
          </p>
        )}
        {!isLoading && !error && entries.length === 0 && (
          <div className="station-timeline-panel__empty">
            {emptyState ?? <p>No timeline activity yet. Check back soon.</p>}
          </div>
        )}
        {!isLoading && !error && entries.length > 0 && (
          <div className="station-timeline-panel__groups">
            {groups.map((group) => (
              <section key={group.key} className="timeline-group">
                <h4 className="timeline-group__label">{group.label}</h4>
                <ul className="timeline-group__entries">
                  {group.entries.map((entry) => {
                    const excerpt = buildPayloadExcerpt(entry.payload);
                    const typeClass = `timeline-entry--${sanitizeTypeForClassName(entry.type)}`;

                    return (
                      <li key={entry.id} className={`timeline-entry ${typeClass}`}>
                        <span className="timeline-entry__icon" aria-hidden="true">
                          {entry.icon}
                        </span>
                        <div className="timeline-entry__content">
                          <header className="timeline-entry__header">
                            <div>
                              <h5>{entry.title}</h5>
                              <div className="timeline-entry__meta">
                                <span className="timeline-entry__type">{entry.type}</span>
                                {entry.source && (
                                  <span className="timeline-entry__source">{entry.source}</span>
                                )}
                              </div>
                              {entry.summary && (
                                <p className="timeline-entry__summary">{entry.summary}</p>
                              )}
                            </div>
                            <time dateTime={entry.occurred_at} className="timeline-entry__timestamp">
                              {formatTimeLabel(entry.occurred_at)}
                            </time>
                          </header>
                          {excerpt && (
                            <pre className="timeline-entry__payload" aria-label="Event payload excerpt">
                              {excerpt}
                            </pre>
                          )}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </section>
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export type { StationTimelinePanelProps };
export default StationTimelinePanel;
