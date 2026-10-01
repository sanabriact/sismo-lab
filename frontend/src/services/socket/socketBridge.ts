import { socketService } from "./socketService";
import { ObservatoryService } from "../seismicObservatory/seismicObservatoryService";
import { applyModeChanged } from "../../utils/mode/ApplyModeChanged";
import { applySnapshot } from "../../utils/mode/ApplySnapshot";
import { maxImbalance } from "../../utils/tree/maxImbalance";
import type { ModeChangedPayload } from "../../models/interfaces/realTime/ModeChangedPayload";
import type { TreeOperation } from "../../models/interfaces/realTime/TreeOperation";
import { applyScenarioEvent } from "../../utils/scenario/ApplyScenario";
import { clockService } from "./clockService";
import type { ClockUpdatedPayload } from "../../models/interfaces/realTime/ClockUpdatedPayload";

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
    socket.on("tree:operation", (operation: TreeOperation) => applyScenarioEvent(operation));
    socket.on("clock:updated", (payload: ClockUpdatedPayload) => clockService.applyUpdate(payload));
    socket.on("connect", loadSnapshot)
}
