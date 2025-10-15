import { useStationAgentActions, useStationDashboard, useTelemetryEvents } from '../../services/api';

const STATION_SLUG = 'toc-s3';

const TOCS3Dashboard = () => {
  const { data: dashboard } = useStationDashboard(STATION_SLUG);
  const { data: agentCatalog } = useStationAgentActions(STATION_SLUG);
  const { data: events = [] } = useTelemetryEvents(STATION_SLUG);

  return (
    <div className="station-dashboard station-dashboard--agentkit">
      <section className="station-summary">
        <h2>{dashboard?.station.name ?? 'TOC-S3'}</h2>
        <p>Mission control and AgentKit orchestration</p>
        <div className="kpi-grid">
          <div className="kpi">
            <span className="kpi-label">Events</span>
            <span className="kpi-value">{dashboard?.metrics.total_events ?? 0}</span>
          </div>
          <div className="kpi">
            <span className="kpi-label">Actions</span>
            <span className="kpi-value">{agentCatalog?.actions.length ?? 0}</span>
          </div>
        </div>
      </section>

      <section className="agent-actions">
        <header>
          <h3>AgentKit Actions</h3>
        </header>
        <ul>
          {agentCatalog?.actions.map((action) => (
            <li key={action.name}>
              <h4>{action.name}</h4>
              <p>{action.description}</p>
              <code>{action.method} {action.endpoint}</code>
            </li>
          ))}
        </ul>
      </section>

      <section className="event-feed">
        <header>
          <h3>Recent Events</h3>
        </header>
        <ul>
          {events.slice(0, 5).map((event) => (
            <li key={event.id}>
              <span>{event.source.name}</span>
              <time>{new Date(event.received_at).toLocaleTimeString()}</time>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};

export default TOCS3Dashboard;
