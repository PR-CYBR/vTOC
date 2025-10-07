import React, { useState, useEffect } from 'react';
import { operationsAPI, missionsAPI, assetsAPI, agentsAPI } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState({
    operations: 0,
    missions: 0,
    assets: 0,
    agents: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [operations, missions, assets, agents] = await Promise.all([
          operationsAPI.getAll(),
          missionsAPI.getAll(),
          assetsAPI.getAll(),
          agentsAPI.getAll(),
        ]);

        setStats({
          operations: operations.data.length,
          missions: missions.data.length,
          assets: assets.data.length,
          agents: agents.data.length,
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Virtual Tactical Operations Center Overview</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card card">
          <h3>Operations</h3>
          <div className="stat-value">{stats.operations}</div>
        </div>
        <div className="stat-card card">
          <h3>Missions</h3>
          <div className="stat-value">{stats.missions}</div>
        </div>
        <div className="stat-card card">
          <h3>Assets</h3>
          <div className="stat-value">{stats.assets}</div>
        </div>
        <div className="stat-card card">
          <h3>Agents</h3>
          <div className="stat-value">{stats.agents}</div>
        </div>
      </div>

      <div className="card">
        <h2>System Status</h2>
        <p style={{ color: '#28a745' }}>✓ All systems operational</p>
      </div>
    </div>
  );
}

export default Dashboard;
