import React, { useState, useEffect } from 'react';
import { agentsAPI } from '../services/api';

function Agents() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await agentsAPI.getAll();
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAgent = async (id) => {
    try {
      await agentsAPI.start(id);
      fetchAgents();
    } catch (error) {
      console.error('Error starting agent:', error);
    }
  };

  const handleStopAgent = async (id) => {
    try {
      await agentsAPI.stop(id);
      fetchAgents();
    } catch (error) {
      console.error('Error stopping agent:', error);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="agents-page">
      <div className="page-header">
        <h1>Automation Agents</h1>
        <p>Manage automated agent systems</p>
      </div>

      <div className="card">
        <div style={{ marginBottom: '20px' }}>
          <button className="button">+ New Agent</button>
        </div>

        {agents.length === 0 ? (
          <p>No agents found. Create your first automation agent to get started.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Last Run</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.id}>
                  <td>{agent.name}</td>
                  <td>{agent.agent_type}</td>
                  <td>
                    <span className={`status-badge status-${agent.status}`}>
                      {agent.status}
                    </span>
                  </td>
                  <td>
                    {agent.last_run
                      ? new Date(agent.last_run).toLocaleString()
                      : 'Never'}
                  </td>
                  <td>
                    {agent.status !== 'running' ? (
                      <button
                        className="button"
                        onClick={() => handleStartAgent(agent.id)}
                      >
                        Start
                      </button>
                    ) : (
                      <button
                        className="button secondary"
                        onClick={() => handleStopAgent(agent.id)}
                      >
                        Stop
                      </button>
                    )}
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

export default Agents;
