import type { ModeChangedPayload } from "../../models/interfaces/realTime/ModeChangedPayload";
import { modeStore } from "../../stores/modeStore";

export function applyModeChanged(payload: ModeChangedPayload): void {
    modeStore.set({
        mode: payload.mode,
        status: payload.status === "changed" ? "idle" : payload.status,
        balanced: payload.balanced,
        maxImbalance: payload.maxImbalance,
        reason: payload.status === "failed" ? "La auditoría no confirmó el equilibrio. Se mantiene el modo estrés."
                                            : null
    })
}