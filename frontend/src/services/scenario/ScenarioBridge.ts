// ------------------------------------------------------------------
// S ce na ri oB ri dg e
// ------------------------------------------------------------------

import { socketService } from "../socket/socketService";
import { applyScenarioPayload, applyScenarioStatus } from "../../utils/scenario/ApplyScenario";
import type { ScenarioLoadedPayload } from "../../models/interfaces/scenery/ScenarioLoadedPayload";
import type { ScenarioStatusResponse } from "../../models/interfaces/scenery/ScenarioStatusResponse";
import { clockService } from "../socket/clockService";

const STATUS_TIMEOUT_MS = 3_000;
let started = false;

// Connects the socket and syncs scenario state; runs only once
export function startScenarioBridge(): void {
    if (started) return;
    started = true;

    const socket = socketService.connect();
    // Apply scenario data pushed by the server
    socket.on("scenario:loaded", (payload: ScenarioLoadedPayload) => void applyScenarioPayload(payload));
    // On every (re)connect, request the current scenario status
    socket.on("connect", () => {
        socket.timeout(STATUS_TIMEOUT_MS).emit(
            "scenario:status",
            (error: Error | null, response?: ScenarioStatusResponse) => {
                // Sync the clock only when the response is valid
                if (!error && response) clockService.setCurrentTime(response.currentTime);
                // Pass null on timeout/error so the status is reset
                void applyScenarioStatus(error || !response ? null: response);
            }
        );
    });
};