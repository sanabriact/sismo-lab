import type { ExecutionMode } from "../../types/observatory/ExecutionMode";

export interface ScenarioLoadedPayload {
    scenarioId: string;
    mode: ExecutionMode;
    stations: number;
    events: number;
}