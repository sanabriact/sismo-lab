// ------------------------------------------------------------------
// A pp ly Sn ap sh ot
// ------------------------------------------------------------------

import type { ExecutionMode } from "../../models/types/observatory/ExecutionMode";
import { modeStore } from "../../stores/mode/modeStore";

// Syncs mode and balance info from a snapshot, only when no change is in progress
export function applySnapshot(mode: ExecutionMode, imbalance: number): void {
    const current = modeStore.getSnapshot();
    // Skip while a mode change is pending, recovering or failed
    if (current.status !== "idle") return;
    modeStore.set({
        ...current,
        mode,
        // AVL tree is balanced when imbalance is at most 1
        balanced: imbalance <= 1,
        maxImbalance: imbalance
    })

}