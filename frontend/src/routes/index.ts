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
const EventList = lazy(() => import('../pages/events/list/EventList'));
const Reports = lazy(() => import('../pages/reports/Reports'));
const Associations = lazy(() => import('../pages/events/associations/Associations'));
const History = lazy(() => import('../pages/history/History'));
const ArchivedEvents = lazy(() => import('../pages/history/ArchivedEvents'));
const DeletedEvents = lazy(() => import('../pages/history/DeletedEvents'));
const HistoricalIds = lazy(() => import('../pages/history/HistoricalIds'));
const Parameters = lazy(() => import('../pages/parameters/Parameters'));

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
        path: "/parameters",
        title: "Parámetros",
        component: Parameters,
    },
    {
        path: "/reports",
        title: "Reportes",
        component: Reports,
        requiresScenario: true,
    },
    {
        path: "/history",
        title: "Histórico",
        component: History,
        requiresScenario: true,
    },
    {
        path: "/history/archived-events",
        title: "Eventos archivados",
        component: ArchivedEvents,
        requiresScenario: true,
        hideInSidebar: true,
    },
    {
        path: "/history/deleted-events",
        title: "Eventos eliminados",
        component: DeletedEvents,
        requiresScenario: true,
        hideInSidebar: true,
    },
    {
        path: "/history/identifiers",
        title: "Identificadores históricos",
        component: HistoricalIds,
        requiresScenario: true,
        hideInSidebar: true,
    },
    {
        path: "/scenario",
        title: "Escenario",
        component: Scenario,
        requiresScenario: true
    },
    {
        path: "/events/list",
        title: "Gestionar eventos",
        component: EventList,
        group: "events",
        requiresScenario: true
    },
    {
        path: "/events/consult",
        title: "Consultar eventos",
        component: ConsultEvent,
        group: "events",
        requiresScenario: true
    },
    {
        path: "/events/associations",
        title: "Asociaciones",
        component: Associations,
        group: "events",
        requiresScenario: true
    },
    {
        path: "/events/create-events",
        title: "Crear eventos",
        component: CreateEvent,
        requiresScenario: true,
        hideInSidebar: true
    },
    /* Here we put :eventId for indicating React that a attribute will go there. */
    {
        path: "/events/correct-event/:eventId",
        title: "Corregir eventos",
        component: CorrectEvent,
        requiresScenario: true,
        hideInSidebar: true
    },
    {
        path: "/events/visualize-trees",
        title: "Visualizar eventos",
        component: VisualizeTrees,
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
