import routes from ".";
import type { AppRoute} from "../models/interfaces/appRoute/AppRoute";

export const getRoutesByGroup = (group: string): AppRoute[] => routes.filter((route) => route.group === group);