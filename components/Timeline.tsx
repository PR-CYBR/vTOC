import { TimelineEntry } from '@/lib/types';
import { formatTime } from '@/lib/time';
import { payloadExcerpt } from '@/lib/utils';

export function TimelineGroup({ date, entries }: { date: string; entries: TimelineEntry[] }) {
  return (
    <section className="timeline-group">
      <div className="timeline-date">{new Date(date).toDateString()}</div>
      <ul className="timeline-list">
        {entries.map(e => (
          <li key={e.id} className={`timeline-entry timeline-entry--${e.type.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
            <span className="timeline-entry__icon">{e.icon ?? '📡'}</span>
            <div className="timeline-entry__content">
              <header className="timeline-entry__header">
                <div>
                  <h5 style={{ margin: 0 }}>{e.title}</h5>
                  <div className="timeline-entry__meta">
                    <span className="timeline-entry__type">{e.type}</span>
                    {e.source && <span className="timeline-entry__source">{e.source}</span>}
                  </div>
                  {e.summary && <p className="timeline-entry__summary" style={{ margin: '.25rem 0 0 0' }}>{e.summary}</p>}
                </div>
                <time className="timeline-entry__timestamp">{formatTime(e.occurred_at)}</time>
              </header>
              {e.payload ? <pre className="timeline-entry__payload">{payloadExcerpt(e.payload)}</pre> : null}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
