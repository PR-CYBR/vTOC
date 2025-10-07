import React, { useState, useEffect } from 'react';
import { operationsAPI } from '../services/api';

function Operations() {
  const [operations, setOperations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOperations();
  }, []);

  const fetchOperations = async () => {
    try {
      const response = await operationsAPI.getAll();
      setOperations(response.data);
    } catch (error) {
      console.error('Error fetching operations:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="operations-page">
      <div className="page-header">
        <h1>Operations</h1>
        <p>Manage tactical operations</p>
      </div>

      <div className="card">
        <div style={{ marginBottom: '20px' }}>
          <button className="button">+ New Operation</button>
        </div>

        {operations.length === 0 ? (
          <p>No operations found. Create your first operation to get started.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Code Name</th>
                <th>Name</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {operations.map((op) => (
                <tr key={op.id}>
                  <td>{op.code_name}</td>
                  <td>{op.name}</td>
                  <td>
                    <span className={`status-badge status-${op.status}`}>
                      {op.status}
                    </span>
                  </td>
                  <td>{op.priority}</td>
                  <td>{new Date(op.created_at).toLocaleDateString()}</td>
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

export default Operations;
