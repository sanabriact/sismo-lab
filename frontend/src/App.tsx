// ------------------------------------------------------------------
// A pp
// ------------------------------------------------------------------

import { Suspense } from 'react';
import DefaultLayout from './layout/DefaultLayout'
import routes from './routes';
import { Navigate, Route, Routes } from "react-router-dom";
import Fallback from './pages/fallback/Fallback';
import Loading from './pages/loading/Loading';
import RequireScenario from './components/scenery/RequireScenario';

// Root component: app routing
function App() {
  return (
    // Shows the loader while lazy pages load
    <Suspense fallback={<Loading />}>
      <Routes>
        {/* Redirect the root path to /home */}
        <Route
          path="/"
          element={<Navigate to="/home" replace/>}
        />
        {/* Pages inside the default layout */}
        <Route element={<DefaultLayout />}>
          {/* Routes that require a loaded scenario are wrapped in RequireScenario */}
          {routes.map(({ path, component: Component, requiresScenario }) => (
            <Route 
            key={path} 
            path={path} 
            element={requiresScenario ? <RequireScenario><Component /></RequireScenario> : <Component />} />
          ))}
        </Route>
        {/* Unknown paths */}
        <Route
          path="*"
          element={
            <Suspense fallback={<Loading />}>
              <Fallback />
            </Suspense>
          }
        />
      </Routes>
    </Suspense>
  );
}

export default App;