import { socketService } from "./socketService";
import { ObservatoryService } from "../seismicObservatory/seismicObservatoryService";
import { applyModeChanged } from "../../utils/mode/ApplyModeChanged";
import { applySnapshot } from "../../utils/mode/ApplySnapshot";
import { maxImbalance } from "../../utils/tree/maxImbalance";
import type { ModeChangedPayload } from "../../models/interfaces/realTime/ModeChangedPayload";

let started = false;

async function loadSnapshot(): Promise<void> {
    const observatory = await ObservatoryService.getObservatory()
    if (!observatory) return;
    applySnapshot(observatory.execution_mode, maxImbalance(observatory.avl_tree?.root ?? null));
}

export function startSocketBridge(): void {
    if (started) return;
    started = true;

    const socket = socketService.connect();
    socket.on("mode:changed", (payload: ModeChangedPayload) => applyModeChanged(payload));
    socket.on("connect", loadSnapshot)
}