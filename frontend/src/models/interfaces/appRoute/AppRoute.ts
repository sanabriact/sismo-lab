// ------------------------------------------------------------------
// A pp Ro ut e
// ------------------------------------------------------------------

import type { ComponentType, LazyExoticComponent } from "react";

export interface AppRoute {
    path: string;
    title: string;
    component: LazyExoticComponent<ComponentType>;
    group?: string;
    requiresScenario?: boolean;
    hideInSidebar?: boolean;
}
