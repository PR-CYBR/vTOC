import Layout from '@/components/Layout';
import { GetStaticPaths, GetStaticProps } from 'next';
import { loadDashboard, loadTimeline } from '@/lib/data';
import { groupByDate } from '@/lib/utils';
import { TimelineGroup } from '@/components/Timeline';
import { StationDashboard, TimelineEntry } from '@/lib/types';
import dynamic from 'next/dynamic';

// Dynamically import Map component to avoid SSR issues with Leaflet
const Map = dynamic(() => import('@/components/Map'), {
  ssr: false,
  loading: () => (
    <div className="map-placeholder">
      Loading map...
    </div>
  ),
});

type Props = { slug: string; dash: StationDashboard; timeline: TimelineEntry[] };

export default function Station({ slug, dash, timeline }: Props) {
  const groups = groupByDate(timeline);
  const dates = Object.keys(groups).sort().reverse(); // newest date first

  return (
    <Layout>
      <aside className="intel-panel">
        <header>
          <div>
            <h2 style={{ margin: 0 }}>
              {dash.station.name}
              <span className={`role-badge role-${dash.station.role.toLowerCase()}`}>{dash.station.role}</span>
            </h2>
            {dash.station.callsign && <p className="intel-subtitle">{dash.station.callsign}</p>}
          </div>
          <div style={{ display: 'flex', gap: '.5rem' }}>
            <button onClick={() => alert('Mock telemetry injected (demo only).')}>Mock telemetry</button>
          </div>
        </header>

        <div className="kpi-grid">
          <div className="kpi">
            <span className="kpi-label">Events</span>
            <div className="kpi-value">{dash.metrics.total_events}</div>
          </div>
          <div className="kpi">
            <span className="kpi-label">Active Sources</span>
            <div className="kpi-value">{dash.metrics.active_sources}</div>
          </div>
        </div>

        {dash.metrics.last_event && (
          <div style={{ padding: '0.75rem 1rem' }}>
            <h3 style={{ margin: '.5rem 0' }}>Latest Signal</h3>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--muted)' }}>
              {new Date(dash.metrics.last_event.occurred_at).toLocaleString()}
            </p>
            <pre className="timeline-entry__payload">
{JSON.stringify(dash.metrics.last_event.payload, null, 2)}
            </pre>
          </div>
        )}

        <div className="station-timeline-panel">
          {dates.map(d => <TimelineGroup key={d} date={d} entries={groups[d]} />)}
        </div>
      </aside>

      <section className="map-section">
        <Map />
      </section>
    </Layout>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const slugs = ['toc-s1','toc-s2','toc-s3','toc-s4'];
  return { paths: slugs.map(slug => ({ params: { slug } })), fallback: false };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const slug = String(params!.slug);
  const dash = await loadDashboard(slug);
  const timeline = await loadTimeline(slug);
  return { props: { slug, dash, timeline } };
};
