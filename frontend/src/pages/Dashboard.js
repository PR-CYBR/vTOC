import React, { useState, useEffect } from 'react';
import {
  operationsAPI,
  missionsAPI,
  assetsAPI,
  agentsAPI,
} from '../services/api';
import MapView from '../components/MapView';
import { fetchTelemetryLayers } from '../services/telemetryAdapter';

const TELEMETRY_REFRESH_MS = 30000;

function Dashboard() {
  const { operations, missions, assets, agents } = useApi();
  const [stats, setStats] = useState({
    operations: 0,
    missions: 0,
    assets: 0,
    agents: 0,
  });
  const [loading, setLoading] = useState(true);
  const [telemetry, setTelemetry] = useState({
    assetLayers: {},
    trackLayers: {},
    center: undefined,
  });
  const [telemetryLoading, setTelemetryLoading] = useState(true);
  const [telemetryError, setTelemetryError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [operationsResponse, missionsResponse, assetsResponse, agentsResponse] =
          await Promise.all([
            operations.getAll(),
            missions.getAll(),
            assets.getAll(),
            agents.getAll(),
          ]);

        setStats({
          operations: operationsResponse.data.length,
          missions: missionsResponse.data.length,
          assets: assetsResponse.data.length,
          agents: agentsResponse.data.length,
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [operations, missions, assets, agents]);

  useEffect(() => {
    let isMounted = true;

    const loadTelemetry = async () => {
      try {
        const layers = await fetchTelemetryLayers();
        if (!isMounted) return;

        setTelemetry({
          assetLayers: layers.assetLayers,
          trackLayers: layers.trackLayers,
          center: layers.center,
        });
        setTelemetryError(null);
      } catch (error) {
        console.error('Error fetching telemetry data:', error);
        if (isMounted) {
          setTelemetryError('Unable to load telemetry feeds. Showing last known information.');
        }
      } finally {
        if (isMounted) {
          setTelemetryLoading(false);
        }
      }
    };

    loadTelemetry();
    const intervalId = window.setInterval(loadTelemetry, TELEMETRY_REFRESH_MS);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="dashboard dashboard-map-layout">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Virtual Tactical Operations Center Overview</p>
      </div>

      <div className="map-panel card">
        <MapView
          assetLayers={telemetry.assetLayers}
          trackLayers={telemetry.trackLayers}
          center={telemetry.center}
        />

        <div className="map-overlay overlay-top-left">
          <div className="stats-grid overlay-grid">
            <div className="stat-card overlay-card">
              <h3>Operations</h3>
              <div className="stat-value">{stats.operations}</div>
            </div>
            <div className="stat-card overlay-card">
              <h3>Missions</h3>
              <div className="stat-value">{stats.missions}</div>
            </div>
            <div className="stat-card overlay-card">
              <h3>Assets</h3>
              <div className="stat-value">{stats.assets}</div>
            </div>
            <div className="stat-card overlay-card">
              <h3>Agents</h3>
              <div className="stat-value">{stats.agents}</div>
            </div>
          </div>
        </div>

        <div className="map-overlay overlay-bottom-left">
          <div className="overlay-card system-status-card">
            <h2>System Status</h2>
            <p className="status-text">✓ All systems operational</p>
          </div>
        </div>

        <div className="map-overlay overlay-top-right">
          <div className="overlay-card telemetry-card">
            <h3>Telemetry Feeds</h3>
            {telemetryLoading ? (
              <p>Loading telemetry…</p>
            ) : telemetryError ? (
              <p className="error-text">{telemetryError}</p>
            ) : (
              <ul>
                {Object.keys(telemetry.assetLayers).map((source) => (
                  <li key={`asset-${source}`}>
                    Assets — <strong>{source}</strong>
                  </li>
                ))}
                {Object.keys(telemetry.trackLayers).map((source) => (
                  <li key={`track-${source}`}>
                    Tracks — <strong>{source}</strong>
                  </li>
                ))}
                {!Object.keys(telemetry.assetLayers).length &&
                  !Object.keys(telemetry.trackLayers).length && <li>No telemetry sources detected.</li>}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
