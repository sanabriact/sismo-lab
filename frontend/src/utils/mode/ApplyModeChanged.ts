// ------------------------------------------------------------------
// A pp ly Mo de Ch an ge d
// ------------------------------------------------------------------

import type { ModeChangedPayload } from "../../models/interfaces/realTime/ModeChangedPayload";
import { modeStore } from "../../stores/mode/modeStore";

// Updates the mode store from a server "mode changed" payload
export function applyModeChanged(payload: ModeChangedPayload): void {
    modeStore.set({
        mode: payload.mode,
        // "changed" means the transition finished, so the store goes back to idle
        status: payload.status === "changed" ? "idle" : payload.status,
        balanced: payload.balanced,
        maxImbalance: payload.maxImbalance,
        // Show an error reason only when the audit failed
        reason: payload.status === "failed" ? "La auditoría no confirmó el equilibrio. Se mantiene el modo estrés."
                                            : null
    })
}