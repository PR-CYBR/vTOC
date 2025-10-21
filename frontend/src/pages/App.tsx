import { useState } from 'react';
import { useMemo, useState } from 'react';
import { NavLink } from 'react-router-dom';

import ChatKitWidget from '../components/chatkit/ChatKitWidget';
import SetupWizard from '../features/setup/SetupWizard';
import AppRouter from '../router';
import SetupWizard from '../features/setup/SetupWizard';
import { useSupabaseSession, useTelemetryEvents } from '../services/api';

const StationNav = () => {
  const items = [
    { path: '/stations/toc-s1', label: 'TOC-S1' },
    { path: '/stations/toc-s2', label: 'TOC-S2' },
    { path: '/stations/toc-s3', label: 'TOC-S3' },
    { path: '/stations/toc-s4', label: 'TOC-S4' },
    { path: '/map', label: 'Map' },
    { path: '/setup', label: 'Setup' },
  ];

  return (
    <nav className="station-nav">
      {items.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) => `station-nav__link${isActive ? ' station-nav__link--active' : ''}`}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
};

const App = () => {
  const [wizardOpen, setWizardOpen] = useState(false);
  const [consoleOpen, setConsoleOpen] = useState(false);
  const [widgetReady, setWidgetReady] = useState(false);
  const defaultStation = import.meta.env.VITE_AGENTKIT_DEFAULT_STATION_CONTEXT ?? 'toc-s1';
  const chatkitConfigured = Boolean(
    import.meta.env.VITE_CHATKIT_API_KEY &&
      import.meta.env.VITE_AGENTKIT_ORG_ID &&
      import.meta.env.VITE_CHATKIT_WIDGET_URL,
  );
  const { data: telemetryEvents = [], isLoading: telemetryLoading } = useTelemetryEvents(defaultStation);
  const { data: supabaseSession } = useSupabaseSession();

  const supabaseCredentials = useMemo(() => {
    if (!supabaseSession) {
      return undefined;
    }

    return {
      accessToken: supabaseSession.access_token,
      refreshToken: supabaseSession.refresh_token,
      userId: supabaseSession.user?.id,
    };
  }, [supabaseSession]);

  const telemetryContext = useMemo(() => {
    const events = telemetryEvents ?? [];
    const lastEventTimestamp = events.reduce<string | undefined>((latest, event) => {
      if (!event.received_at) {
        return latest;
      }

      if (!latest) {
        return event.received_at;
      }

      const current = new Date(event.received_at).getTime();
      const previous = new Date(latest).getTime();
      return current > previous ? event.received_at : latest;
    }, undefined);

    return {
      events,
      lastEventTimestamp,
      defaultStation,
      credentials: supabaseCredentials,
    };
  }, [defaultStation, supabaseCredentials, telemetryEvents]);

  const chatConsoleLoading = consoleOpen && (!widgetReady || telemetryLoading);

  return (
    <div className="station-shell">
      <header className="station-header">
        <h1>vTOC Station Command</h1>
        <StationNav />
        <button
          type="button"
          className="setup-wizard__trigger"
          onClick={() => setWizardOpen(true)}
        >
          Launch setup wizard
        </button>
        {chatkitConfigured ? (
          <button
            type="button"
            className="setup-wizard__trigger"
            onClick={() => setConsoleOpen((value) => !value)}
          >
            {consoleOpen ? 'Hide operations console' : 'Open operations console'}
          </button>
        ) : null}
      </header>
      <main className="station-content">
        <AppRouter />
      </main>
      <SetupWizard open={wizardOpen} onClose={() => setWizardOpen(false)} />
      {chatkitConfigured ? (
        <aside className="chatkit-console" aria-live="polite">
          {chatConsoleLoading ? (
            <div className="chatkit-console__loading" role="status">
              Loading operations console…
            </div>
          ) : null}
          <ChatKitWidget
            open={consoleOpen && !chatConsoleLoading}
            telemetry={telemetryContext}
            onReady={() => setWidgetReady(true)}
            className="chatkit-console__widget"
          />
        </aside>
      ) : null}
    </div>
  );
};

export default App;
