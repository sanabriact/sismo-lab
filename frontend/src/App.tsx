import { Suspense } from 'react';
import DefaultLayout from './layout/DefaultLayout'
import routes from './routes';
import { Route, Routes } from "react-router-dom";
import Fallback from './pages/Fallback/Fallback';

function App() {
  return (
    <Suspense fallback={<div>Cargando...</div>}>
      <Routes>
        <Route element={<DefaultLayout />}>
          {routes.map(({ path, component: Component }) => (
            <Route key={path} path={path} element={<Component />} />
          ))}
        </Route>
        <Route
          path="*"
          element={
            <Suspense fallback={<div>Cargando...</div>}>
              <Fallback />
            </Suspense>
          }
        />
      </Routes>
    </Suspense>
  );
}
export default App;