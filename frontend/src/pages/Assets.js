import React, { useState, useEffect } from 'react';
import { useApi } from '../services/api';

function Assets() {
  const { assets } = useApi();
  const [assetsList, setAssetsList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const response = await assets.getAll();
        setAssetsList(response.data);
      } catch (error) {
        console.error('Error fetching assets:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAssets();
  }, [assets]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="assets-page">
      <div className="page-header">
        <h1>Assets</h1>
        <p>Manage resources and equipment</p>
      </div>

      <div className="card">
        <div style={{ marginBottom: '20px' }}>
          <button className="button">+ New Asset</button>
        </div>

        {assetsList.length === 0 ? (
          <p>No assets found. Register your first asset to get started.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Location</th>
                <th>Assigned To</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {assetsList.map((asset) => (
                <tr key={asset.id}>
                  <td>{asset.name}</td>
                  <td>{asset.asset_type}</td>
                  <td>
                    <span className={`status-badge status-${asset.status}`}>
                      {asset.status}
                    </span>
                  </td>
                  <td>{asset.location || 'N/A'}</td>
                  <td>{asset.assigned_to || 'Unassigned'}</td>
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

export default Assets;
