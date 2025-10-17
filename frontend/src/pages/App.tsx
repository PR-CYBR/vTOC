import { useState } from 'react';
import { Navigate, NavLink, Route, Routes } from 'react-router-dom';

import TOCS1Dashboard from './stations/TOCS1';
import TOCS2Dashboard from './stations/TOCS2';
import TOCS3Dashboard from './stations/TOCS3';
import TOCS4Dashboard from './stations/TOCS4';
import SetupWizard from '../components/setup/SetupWizard';

const StationNav = () => {
  const items = [
    { path: '/stations/toc-s1', label: 'TOC-S1' },
    { path: '/stations/toc-s2', label: 'TOC-S2' },
    { path: '/stations/toc-s3', label: 'TOC-S3' },
    { path: '/stations/toc-s4', label: 'TOC-S4' }
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
        <Routes>
          <Route path="/" element={<Navigate to="/stations/toc-s1" replace />} />
          <Route path="/stations/toc-s1" element={<TOCS1Dashboard />} />
          <Route path="/stations/toc-s2" element={<TOCS2Dashboard />} />
          <Route path="/stations/toc-s3" element={<TOCS3Dashboard />} />
          <Route path="/stations/toc-s4" element={<TOCS4Dashboard />} />
        </Routes>
      </main>
      <SetupWizard open={wizardOpen} onClose={() => setWizardOpen(false)} />
    </div>
  );
};

export default App;
