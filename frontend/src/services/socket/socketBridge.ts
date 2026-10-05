// ------------------------------------------------------------------
// s oc ke tB ri dg e
// ------------------------------------------------------------------

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
import { actionStackService } from "./actionStackService";

let started = false;

// Fetches the observatory and syncs execution mode and tree imbalance
async function loadSnapshot(): Promise<void> {
    const observatory = await ObservatoryService.getObservatory()
    if (!observatory) return;
    applySnapshot(observatory.execution_mode, maxImbalance(observatory.avl_tree?.root ?? null));
}

// Registers all real-time socket listeners; runs only once
export function startSocketBridge(): void {
    if (started) return;
    started = true;

    const socket = socketService.connect();
    // Undo updates
    actionStackService.subscribeToUpdates();
    // Execution mode changes
    socket.on("mode:changed", (payload: ModeChangedPayload) => applyModeChanged(payload));
    // Tree operations
    socket.on("tree:operation", (operation: TreeOperation) => applyScenarioEvent(operation));
    // Clock updates
    socket.on("clock:updated", (payload: ClockUpdatedPayload) => clockService.applyUpdate(payload));
    // Resync state on every (re)connect
    socket.on("connect", loadSnapshot)
}