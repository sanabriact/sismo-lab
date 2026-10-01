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
const Scenario = lazy(() => import ('../pages/scenery/Scenery'));
const LoadScenario = lazy(() => import ('../pages/load/loadScenario'));
const VerifyStructure = lazy(() => import('../pages/events/verify/VerifyStructure'));

/* Adding components to each route */
const coreRoutes: AppRoute[] = [
    {
        path: "/home",
        title: "Inicio",
        component: Home
    },
    {
        path: "/load-scenario",
        title: "Cargar escenario",
        component: LoadScenario,
    },
    {
        path: "/scenario",
        title: "Escenario",
        component: Scenario,
        requiresScenario: true
    },
    {
        path: "/events/create-events",
        title: "Crear eventos",
        component: CreateEvent,
        group: "events",
        requiresScenario: true
    },
    {
        path: "/events/visualize-trees",
        title: "Visualizar eventos",
        component: VisualizeTrees,
        group: "events",
        requiresScenario: true
    },
    {
        path: "/events/check-events",
        title: "Marcar eventos",
        component: CheckEvent,
        group: "events",
        requiresScenario: true
    },
    {
        path: "/events/consult-events",
        title: "Consultar eventos",
        component: ConsultEvent,
        group: "events",
        requiresScenario: true
    },
    {
        path: "/events/correct-events",
        title: "Corregir eventos",
        component: CorrectEvent,
        group: "events",
        requiresScenario: true
    },
    
    {
        path: "/events/delete-events",
        title: "Eliminar eventos",
        component: DeleteEvent,
        group: "events",
        requiresScenario: true
    },
    {
        path: "/events/verify-structure",
        title: "Verificar estructura",
        component: VerifyStructure,
        group: "events",
        requiresScenario: true
    }
]

const routes = [...coreRoutes]
export default routes;