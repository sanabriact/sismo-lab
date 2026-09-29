import type { ExecutionMode } from "../../models/types/observatory/ExecutionMode";
import { modeStore } from "../../stores/modeStore";

export function applySnapshot(mode: ExecutionMode, imbalance: number): void {
    const current = modeStore.getSnapshot();
    if (current.status !== "idle") return;
    modeStore.set({
        ...current,
        mode,
        balanced: imbalance <= 1,
        maxImbalance: imbalance
    })

}