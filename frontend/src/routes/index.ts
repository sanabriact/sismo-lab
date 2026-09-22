import { lazy, type ComponentType, type LazyExoticComponent } from 'react';

interface AppRoute {
    path: string;
    title: string;
    component: LazyExoticComponent<ComponentType>;
}

const Home = lazy(() => import('../pages/Home/Home'));
const coreRoutes: AppRoute[] = [
    {
        path: "/home",
        title: "Inicio",
        component: Home
    }
]

const routes = [...coreRoutes]
export default routes;