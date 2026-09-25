import { lazy } from 'react';
import type { AppRoute } from '../models/interfaces/appRoute/AppRoute';

/* Import routes components */
const Home = lazy(() => import('../pages/home/Home'));
const VisualizeTrees = lazy(() => import('../pages/events/visualize/VisualizeTrees'));
const CheckEvent = lazy(() => import ('../pages/events/check/CheckEvent'));
const ConsultEvent = lazy(() => import ('../pages/events/consult/ConsultEvent'));
const CorrectEvent = lazy(() => import ('../pages/events/correct/CorrectEvent'));
const CreateEvent = lazy(() => import ('../pages/events/create/CreateEvent'));
const DeleteEvent = lazy (() => import ('../pages/events/delete/DeleteEvent'));
const Scenery = lazy(() => import ('../pages/scenery/Scenery'));

/* Adding components to each route */
const coreRoutes: AppRoute[] = [
    {
        path: "/home",
        title: "Inicio",
        component: Home
    },
    {
        path: "/escenary",
        title: "Escenario",
        component: Scenery
    },
    {
        path: "/events/visualize-trees",
        title: "Visualizar eventos",
        component: VisualizeTrees,
        group: "events"
    },
    {
        path: "/events/check-events",
        title: "Marcar eventos",
        component: CheckEvent,
        group: "events"
    },
    {
        path: "/events/consult-events",
        title: "Consultar eventos",
        component: ConsultEvent,
        group: "events"
    },
    {
        path: "/events/correct-events",
        title: "Corregir eventos",
        component: CorrectEvent,
        group: "events"
    },
    {
        path: "/events/create-events",
        title: "Crear eventos",
        component: CreateEvent,
        group: "events"
    },
    {
        path: "/events/delete-events",
        title: "Eliminar eventos",
        component: DeleteEvent,
        group: "events"
    }
]

const routes = [...coreRoutes]
export default routes;