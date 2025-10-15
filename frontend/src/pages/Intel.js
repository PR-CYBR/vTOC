import React, { useState, useEffect } from 'react';
import { useApi } from '../services/api';

function Intel() {
  const { intel } = useApi();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await intel.getAll();
        setReports(response.data);
      } catch (error) {
        console.error('Error fetching intelligence reports:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [intel]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="intel-page">
      <div className="page-header">
        <h1>Intelligence</h1>
        <p>Intelligence reports and analysis</p>
      </div>

      <div className="card">
        <div style={{ marginBottom: '20px' }}>
          <button className="button">+ New Report</button>
        </div>

        {reports.length === 0 ? (
          <p>No intelligence reports found. Create your first report to get started.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Classification</th>
                <th>Source</th>
                <th>Reliability</th>
                <th>Reported By</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td>{report.title}</td>
                  <td>{report.classification}</td>
                  <td>{report.source || 'N/A'}</td>
                  <td>{report.reliability || 'N/A'}</td>
                  <td>{report.reported_by || 'N/A'}</td>
                  <td>{new Date(report.report_date).toLocaleDateString()}</td>
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

export default Intel;
