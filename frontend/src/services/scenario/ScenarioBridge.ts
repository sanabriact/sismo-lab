import { socketService } from "../socket/socketService";
import { applyScenarioPayload, applyScenarioStatus } from "../../utils/scenario/ApplyScenario";
import type { ScenarioLoadedPayload } from "../../models/interfaces/scenery/ScenarioLoadedPayload";
import type { ScenarioStatusResponse } from "../../models/interfaces/scenery/ScenarioStatusResponse";

const STATUS_TIMEOUT_MS = 3_000;
let started = false;

export function startScenarioBridge(): void {
    if (started) return;
    started = true;

    const socket = socketService.connect();
    socket.on("scenario:loaded", (payload: ScenarioLoadedPayload) => applyScenarioPayload(payload));
    socket.on("connect", () => {
        socket.timeout(STATUS_TIMEOUT_MS).emit(
            "scenario:status",
            (error: Error | null, response?: ScenarioStatusResponse) => {
                applyScenarioStatus(error || !response ? null: response);
            }
        );
    });
};