// ------------------------------------------------------------------
// S ce na ri oS to re
// ------------------------------------------------------------------

import type { ScenarioState } from "../../models/interfaces/scenery/ScenarioState";
import { Observable } from "../Observable";

// Global scenario state: load status, source, messages and map data (zones, stations, events)
export const scenarioStore = new Observable<ScenarioState>({
    hydrated: false,
    loaded: false,
    scenarioId: null,
    operation: "idle",
    source: null,
    message: null,
    issues: [],
    zones: [],
    stations: [],
    events: [],
    summary: null
});