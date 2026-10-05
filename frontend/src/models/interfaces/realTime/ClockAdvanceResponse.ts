// ------------------------------------------------------------------
// C lo ck Ad va nc eR es po ns e
// ------------------------------------------------------------------

import type { ClockUpdatedPayload } from "./ClockUpdatedPayload";

export interface ClockAdvanceResponse {
    ok: boolean;
    reason?: string;
    clock?: ClockUpdatedPayload;
    currentTime?: string;
}
