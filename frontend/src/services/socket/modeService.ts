// ------------------------------------------------------------------
// m od eS er vi ce
// ------------------------------------------------------------------

import { socketService } from "./socketService";
import { modeStore } from "../../stores/mode/modeStore";
import type { ExecutionMode } from "../../models/types/observatory/ExecutionMode";
import type { ModeSetResponse } from "../../models/interfaces/realTime/ModeSetResponse";

const TIMEOUT_MS = 3_000;
const REASONS: Record<string, string> = {
    no_scenario: "Carga un escenario primero",
    invalid_mode: "Modo no válido."
};

class ModeService {
    request(mode: ExecutionMode): void {
        const current = modeStore.getSnapshot();
        if (current.status === "pending" || current.status === "recovering") return;

        modeStore.set({
            ...current,
            status: "pending",
            reason: null
        });

        socketService.connect().timeout(TIMEOUT_MS).emit(
            "mode:set", { mode }, (error: Error | null, response?: ModeSetResponse) => {
                const actual = modeStore.getSnapshot();
                console.log("Actual: " + actual.mode)
                console.log("Modo: " + mode)
                console.log("Error: " + error)
                console.log("Respuesta: " + response)
                if (error || !response) {
                    modeStore.set({
                        ...actual,
                        status: "failed",
                        reason: "El servidor no respondió."
                    })
                    return;
                }

                if (!response.ok && response.reason){
                    modeStore.set({
                        ...actual,
                        status: "idle",
                        reason: REASONS[response.reason] ?? "No se pudo cambiar el modo."
                    });
                    return;
                }

                if (response.ok && actual.status === "pending" && response.mode) {
                    modeStore.set({
                        ...actual,
                        mode: response.mode,
                        status: "idle"
                    })
                }
            }
        )
    }
}

export const modeService = new ModeService();