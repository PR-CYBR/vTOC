import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

function Navigation() {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h2>vTOC</h2>
        <span>Virtual Tactical Operations Center</span>
      </div>
      <ul className="nav-links">
        <li>
          <Link to="/" className={isActive('/')}>
            Dashboard
          </Link>
        </li>
        <li>
          <Link to="/operations" className={isActive('/operations')}>
            Operations
          </Link>
        </li>
        <li>
          <Link to="/missions" className={isActive('/missions')}>
            Missions
          </Link>
        </li>
        <li>
          <Link to="/assets" className={isActive('/assets')}>
            Assets
          </Link>
        </li>
        <li>
          <Link to="/intel" className={isActive('/intel')}>
            Intelligence
          </Link>
        </li>
        <li>
          <Link to="/agents" className={isActive('/agents')}>
            Agents
          </Link>
        </li>
      </ul>
    </nav>
  );
}

export default Navigation;
