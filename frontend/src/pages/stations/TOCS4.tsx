import { useStations, useStationDashboard } from '../../services/api';
import StationTimelinePanel from '../../components/telemetry/StationTimelinePanel';

const STATION_SLUG = 'toc-s4';

const TOCS4Dashboard = () => {
  const { data: dashboard } = useStationDashboard(STATION_SLUG);
  const { data: stations = [] } = useStations();

  return (
    <div className="station-dashboard station-dashboard--overview">
      <section className="station-summary">
        <h2>{dashboard?.station.name ?? 'TOC-S4'}</h2>
        <p>Strategic oversight and readiness posture</p>
        <div className="kpi-grid">
          <div className="kpi">
            <span className="kpi-label">Active sources</span>
            <span className="kpi-value">{dashboard?.metrics.active_sources ?? 0}</span>
          </div>
          <div className="kpi">
            <span className="kpi-label">Total events</span>
            <span className="kpi-value">{dashboard?.metrics.total_events ?? 0}</span>
          </div>
        </div>
      </section>

      <StationTimelinePanel stationSlug={STATION_SLUG} className="station-timeline-panel--card" />

      <section className="station-table">
        <header>
          <h3>Fleet Readiness</h3>
          <p>All stations reporting</p>
        </header>
        <table>
          <thead>
            <tr>
              <th>Station</th>
              <th>Timezone</th>
              <th>Schema</th>
            </tr>
          </thead>
          <tbody>
            {stations.map((station) => (
              <tr key={station.id}>
                <td>{station.name}</td>
                <td>{station.timezone}</td>
                <td>{station.telemetry_schema ?? 'default'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
};

export default TOCS4Dashboard;
