import type { ScenarioLoadedPayload } from "./ScenarioLoadedPayload";

export interface ScenarioLoadedResponse {
    ok: boolean;
    reason?: string;
    issues?: string[];
    scenario?: ScenarioLoadedPayload;
}