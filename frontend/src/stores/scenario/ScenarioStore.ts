import type { ScenarioState } from "../../models/interfaces/scenery/ScenarioState";
import { Observable } from "../Observable";

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
