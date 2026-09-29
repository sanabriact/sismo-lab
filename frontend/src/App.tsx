import { Suspense } from 'react';
import DefaultLayout from './layout/DefaultLayout'
import routes from './routes';
import { Navigate, Route, Routes } from "react-router-dom";
import Fallback from './pages/fallback/Fallback';
import Loading from './pages/loading/Loading';
import RequireScenario from './components/scenery/RequireScenario';

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route
          path="/"
          element={<Navigate to="/home" replace/>}
        />
        <Route element={<DefaultLayout />}>
          {routes.map(({ path, component: Component, requiresScenario }) => (
            <Route 
            key={path} 
            path={path} 
            element={requiresScenario ? <RequireScenario><Component /></RequireScenario> : <Component />} />
          ))}
        </Route>
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