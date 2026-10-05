import { socketService } from "./socketService";
import { clockStore } from "../../stores/clock/clockStore";
import type { ClockAdvanceResponse } from "../../models/interfaces/realTime/ClockAdvanceResponse";
import type { ClockUpdatedPayload } from "../../models/interfaces/realTime/ClockUpdatedPayload";

const TIMEOUT_MS = 3_000;

// Backend error codes mapped to user-facing messages
const REASONS: Record<string, string> = {
    no_scenario: "Carga un escenario primero.",
    busy: "El escenario está ocupado recuperando su estructura.",
    missing_clock_advance_value: "Indica cuántas horas deseas avanzar.",
};

// Stores the new time and resets the operation state
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
    // Sets the time directly (null clears it)
    setCurrentTime(currentTime: string | null): void {
        const current = clockStore.getSnapshot();
        clockStore.set({
            ...current,
            currentTime,
            operation: "idle",
            message: null,
        });
    }

    // Applies a clock update pushed by the server
    applyUpdate(payload: ClockUpdatedPayload): void {
        applyClockPayload(payload);
    }

    // Requests the server to advance the clock by N hours
    advanceHours(hours: number): void {
        const current = clockStore.getSnapshot();
        // Ignore if a request is already in flight
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
                // Re-read the store: it may have changed while waiting
                const actual = clockStore.getSnapshot();
                // Timeout or empty response
                if (error || !response) {
                    clockStore.set({
                        ...actual,
                        operation: "failed",
                        message: "El servidor no respondió.",
                    });
                    return;
                }

                // Backend rejected the request
                if (!response.ok || !response.clock) {
                    clockStore.set({
                        ...actual,
                        operation: "failed",
                        message: REASONS[response.reason ?? ""] ?? "No se pudo avanzar el reloj.",
                    });
                    return;
                }

                // Success: apply the new time
                applyClockPayload(response.clock);
            },
        );
    }
}

export const clockService = new ClockService();