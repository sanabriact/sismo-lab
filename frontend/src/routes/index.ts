import { lazy } from 'react';
import type { AppRoute } from '../models/interfaces/AppRoute/AppRoute';

/* Import routes components */
const Home = lazy(() => import('../pages/home/Home'));
const VisualizeTrees = lazy(() => import('../pages/events/visualize/VisualizeTrees'));
const CheckEvent = lazy(() => import ('../pages/events/check/CheckEvent'));
const ConsultEvent = lazy(() => import ('../pages/events/consult/ConsultEvent'));
const CorrectEvent = lazy(() => import ('../pages/events/correct/CorrectEvent'));
const CreateEvent = lazy(() => import ('../pages/events/create/CreateEvent'));
const DeleteEvent = lazy (() => import ('../pages/events/delete/DeleteEvent'));

/* Adding components to each route */
const coreRoutes: AppRoute[] = [
    {
        path: "/home",
        title: "Inicio",
        component: Home
    },
    /* {
        path: "/events/visualize-trees",
        title: "Visualizar eventos",
        component: VisualizeTrees
    },
    {
        path: "/events/check-events",
        title: "Marcar eventos",
        component: CheckEvent
    },
    {
        path: "/events/consult-events",
        title: "Consultar eventos",
        component: ConsultEvent
    },
    {
        path: "/events/correct-events",
        title: "Corregir eventos",
        component: CorrectEvent
    },
    {
        path: "/events/create-events",
        title: "Crear eventos",
        component: CreateEvent
    },
    {
        path: "/events/delete-events",
        title: "Eliminar eventos",
        component: DeleteEvent
    } */
]

const routes = [...coreRoutes]
export default routes;