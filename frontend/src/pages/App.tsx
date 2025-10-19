import { useState } from 'react';
import { NavLink } from 'react-router-dom';

import AppRouter from '../router';
import SetupWizard from '../features/setup/SetupWizard';

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
      </header>
      <main className="station-content">
        <AppRouter />
      </main>
      <SetupWizard open={wizardOpen} onClose={() => setWizardOpen(false)} />
    </div>
  );
};

export default App;
