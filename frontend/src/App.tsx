import { Suspense } from 'react';
import DefaultLayout from './layout/DefaultLayout'
import routes from './routes';
import { Route, Routes } from "react-router-dom";
import Fallback from './pages/fallback/Fallback';
import Loading from './pages/loading/Loading';

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route element={<DefaultLayout />}>
          {routes.map(({ path, component: Component }) => (
            <Route key={path} path={path} element={<Component />} />
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