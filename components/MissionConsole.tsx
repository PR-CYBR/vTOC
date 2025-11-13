'use client';

import { useState } from 'react';

export default function MissionConsole() {
  const [telemetryMessage, setTelemetryMessage] = useState('');
  const [agentCommand, setAgentCommand] = useState('');
  const [notifications, setNotifications] = useState<{ id: number; message: string; type: 'success' | 'info' }[]>([]);
  const [nextId, setNextId] = useState(1);

  const addNotification = (message: string, type: 'success' | 'info' = 'success') => {
    const id = nextId;
    setNextId(id + 1);
    setNotifications((prev) => [...prev, { id, message, type }]);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 3000);
  };

  const handleTelemetrySend = () => {
    if (!telemetryMessage.trim()) {
      addNotification('Please enter a telemetry message', 'info');
      return;
    }

    // Simulate backend interaction
    console.log('Telemetry submitted:', telemetryMessage);
    addNotification('✓ Telemetry submitted (simulated)', 'success');
    setTelemetryMessage('');
  };

  const handleAgentTrigger = () => {
    if (!agentCommand.trim()) {
      addNotification('Please enter an agent command', 'info');
      return;
    }

    // Simulate GitHub Action or API call
    console.log('Agent command triggered:', agentCommand);
    addNotification('✓ Agent triggered (simulated)', 'success');
    setAgentCommand('');
  };

  return (
    <div className="mission-console">
      {/* Toast notifications */}
      {notifications.length > 0 && (
        <div className="toast-container">
          {notifications.map((notification) => (
            <div key={notification.id} className={`toast toast--${notification.type}`}>
              {notification.message}
            </div>
          ))}
        </div>
      )}

      <div className="mission-console-header">
        <strong>Mission Console</strong>
      </div>

      {/* Telemetry form */}
      <div className="mission-form">
        <label className="mission-label">Send Telemetry</label>
        <textarea
          className="mission-input"
          placeholder="Enter telemetry data or message..."
          value={telemetryMessage}
          onChange={(e) => setTelemetryMessage(e.target.value)}
          rows={3}
        />
        <button
          className="mission-btn mission-btn--primary"
          onClick={handleTelemetrySend}
        >
          📡 Send Telemetry
        </button>
      </div>

      {/* Agent trigger form */}
      <div className="mission-form">
        <label className="mission-label">Trigger Agent</label>
        <input
          type="text"
          className="mission-input"
          placeholder="Enter agent command..."
          value={agentCommand}
          onChange={(e) => setAgentCommand(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAgentTrigger()}
        />
        <button
          className="mission-btn mission-btn--secondary"
          onClick={handleAgentTrigger}
        >
          🤖 Trigger Agent
        </button>
      </div>

      {/* Status display */}
      <div className="mission-status">
        <div className="mission-status-label">Connection Status</div>
        <div className="mission-status-value">
          <span className="status-indicator status-indicator--simulated"></span>
          Simulated Mode
        </div>
      </div>
    </div>
  );
}
