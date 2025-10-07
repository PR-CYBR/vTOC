import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import Operations from './pages/Operations';
import Missions from './pages/Missions';
import Assets from './pages/Assets';
import Intel from './pages/Intel';
import Agents from './pages/Agents';
import Navigation from './components/Navigation';

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <div className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/operations" element={<Operations />} />
            <Route path="/missions" element={<Missions />} />
            <Route path="/assets" element={<Assets />} />
            <Route path="/intel" element={<Intel />} />
            <Route path="/agents" element={<Agents />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
