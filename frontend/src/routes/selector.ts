import routes from ".";
import type { AppRoute } from "../models/interfaces/appRoute/AppRoute";

/* 
    Here we generate a list of routes depending of a group sent via parameter.
*/
export const getRoutesByGroup = (group: string): AppRoute[] => routes.filter((route) => route.group === group);