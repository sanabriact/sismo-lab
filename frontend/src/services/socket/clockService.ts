import { socketService } from "./socketService";
import { clockStore } from "../../stores/clock/clockStore";
import type { ClockAdvanceResponse } from "../../models/interfaces/realTime/ClockAdvanceResponse";
import type { ClockUpdatedPayload } from "../../models/interfaces/realTime/ClockUpdatedPayload";

const TIMEOUT_MS = 3_000;

const REASONS: Record<string, string> = {
    no_scenario: "Carga un escenario primero.",
    busy: "El escenario está ocupado recuperando su estructura.",
    missing_clock_advance_value: "Indica cuántas horas deseas avanzar.",
};

function applyClockPayload(payload: ClockUpdatedPayload): void {
    const current = clockStore.getSnapshot();
    clockStore.set({
        ...current,
        currentTime: payload.currentTime,
        operation: "idle",
        message: null,
    });
}

class ClockService {
    setCurrentTime(currentTime: string | null): void {
        const current = clockStore.getSnapshot();
        clockStore.set({
            ...current,
            currentTime,
            operation: "idle",
            message: null,
        });
    }

    applyUpdate(payload: ClockUpdatedPayload): void {
        applyClockPayload(payload);
    }

    advanceHours(hours: number): void {
        const current = clockStore.getSnapshot();
        if (current.operation === "pending") return;

        clockStore.set({
            ...current,
            operation: "pending",
            message: null,
        });

        socketService.connect().timeout(TIMEOUT_MS).emit(
            "clock:advance",
            { hours },
            (error: Error | null, response?: ClockAdvanceResponse) => {
                const actual = clockStore.getSnapshot();
                if (error || !response) {
                    clockStore.set({
                        ...actual,
                        operation: "failed",
                        message: "El servidor no respondió.",
                    });
                    return;
                }

                if (!response.ok || !response.clock) {
                    clockStore.set({
                        ...actual,
                        operation: "failed",
                        message: REASONS[response.reason ?? ""] ?? "No se pudo avanzar el reloj.",
                    });
                    return;
                }

                applyClockPayload(response.clock);
            },
        );
    }
}

export const clockService = new ClockService();
