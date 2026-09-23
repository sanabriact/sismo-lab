import { lazy } from 'react';
import type { AppRoute } from '../models/interfaces/AppRoute/AppRoute';

/* Import routes components */
const Home = lazy(() => import('../pages/home/Home'));

/* Adding components to each route */
const coreRoutes: AppRoute[] = [
    {
        path: "/home",
        title: "Inicio",
        component: Home
    }
]

const routes = [...coreRoutes]
export default routes;