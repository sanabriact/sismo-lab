// ------------------------------------------------------------------
// S ce na ri oL oa de dR es po ns e
// ------------------------------------------------------------------

import type { ScenarioLoadedPayload } from "./ScenarioLoadedPayload";

export interface ScenarioLoadedResponse {
    ok: boolean;
    reason?: string;
    issues?: string[];
    scenario?: ScenarioLoadedPayload;
}