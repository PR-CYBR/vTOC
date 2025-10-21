import { useStationDashboard, useStationTasks } from '../../services/api';
import StationTimelinePanel from '../../components/telemetry/StationTimelinePanel';

const STATION_SLUG = 'toc-s2';

const TOCS2Dashboard = () => {
  const { data: dashboard } = useStationDashboard(STATION_SLUG);
  const { data: taskQueue, isLoading } = useStationTasks(STATION_SLUG);

  return (
    <div className="station-dashboard station-dashboard--tasks">
      <section className="station-summary">
        <h2>{dashboard?.station.name ?? 'TOC-S2'}</h2>
        <p>Airborne ISR and tasking cell</p>
        <div className="kpi-grid">
          <div className="kpi">
            <span className="kpi-label">Active sources</span>
            <span className="kpi-value">{dashboard?.metrics.active_sources ?? 0}</span>
          </div>
          <div className="kpi">
            <span className="kpi-label">Telemetry events</span>
            <span className="kpi-value">{dashboard?.metrics.total_events ?? 0}</span>
          </div>
        </div>
      </section>

      <StationTimelinePanel stationSlug={STATION_SLUG} className="station-timeline-panel--card" />

      <section className="task-list">
        <header>
          <h3>Task Queue</h3>
          <span>{taskQueue?.tasks.length ?? 0} tasks</span>
        </header>
        {isLoading && <p>Loading tasks…</p>}
        {!isLoading && (taskQueue?.tasks.length ?? 0) === 0 && (
          <p>No queued tasks. Agents are on standby.</p>
        )}
        <ul>
          {taskQueue?.tasks.map((task) => (
            <li key={task.id} className={`task task--${task.status}`}>
              <div>
                <h4>{task.title}</h4>
                <p>Priority: {task.priority}</p>
                <p>Status: {task.status}</p>
              </div>
              <dl>
                <div>
                  <dt>Assigned</dt>
                  <dd>{new Date(task.created_at).toLocaleString()}</dd>
                </div>
                {task.due_at && (
                  <div>
                    <dt>Updated</dt>
                    <dd>{new Date(task.due_at).toLocaleString()}</dd>
                  </div>
                )}
              </dl>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};

export default TOCS2Dashboard;
