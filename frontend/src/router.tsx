import { Navigate, RouteObject, useRoutes } from 'react-router-dom';

import SetupWizard from './features/setup/SetupWizard';
import MapPage from './pages/Map';
import TOCS1Dashboard from './pages/stations/TOCS1';
import TOCS2Dashboard from './pages/stations/TOCS2';
import TOCS3Dashboard from './pages/stations/TOCS3';
import TOCS4Dashboard from './pages/stations/TOCS4';

const routes: RouteObject[] = [
  { path: '/', element: <Navigate to="/stations/toc-s1" replace /> },
  { path: '/stations/toc-s1', element: <TOCS1Dashboard /> },
  { path: '/stations/toc-s2', element: <TOCS2Dashboard /> },
  { path: '/stations/toc-s3', element: <TOCS3Dashboard /> },
  { path: '/stations/toc-s4', element: <TOCS4Dashboard /> },
  { path: '/map', element: <MapPage /> },
  { path: '/setup', element: <SetupWizard /> },
];

const AppRouter = () => {
  return useRoutes(routes);
};

export default AppRouter;
