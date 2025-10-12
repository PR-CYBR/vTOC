import React, { useState, useEffect } from 'react';
import { missionsAPI } from '../services/api';

function Missions() {
  const [missions, setMissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMissions();
  }, []);

  const fetchMissions = async () => {
    try {
      const response = await missionsAPI.getAll();
      setMissions(response.data);
    } catch (error) {
      console.error('Error fetching missions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="missions-page">
      <div className="page-header">
        <h1>Missions</h1>
        <p>Track and manage mission objectives</p>
      </div>

      <div className="card">
        <div style={{ marginBottom: '20px' }}>
          <button className="button">+ New Mission</button>
        </div>

        {missions.length === 0 ? (
          <p>No missions found. Create your first mission to get started.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Assigned To</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {missions.map((mission) => (
                <tr key={mission.id}>
                  <td>{mission.name}</td>
                  <td>
                    <span className={`status-badge status-${mission.status}`}>
                      {mission.status}
                    </span>
                  </td>
                  <td>{mission.priority}</td>
                  <td>{mission.assigned_to || 'Unassigned'}</td>
                  <td>{new Date(mission.created_at).toLocaleDateString()}</td>
                  <td>
                    <button className="button secondary">View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Missions;
