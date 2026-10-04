import type { ManualEventPayload } from "../../models/interfaces/events/ManualEventPayload";
import type { UpdateEventPayload } from "../../models/interfaces/events/UpdateEventPayload";
import type { SocketResponse } from "../../models/interfaces/socket/SocketResponse";
import type { UpdateEventResponse } from "../../models/interfaces/socket/UpdateEventResponse";
import { socketService } from "./socketService";

// Maximum time to wait for a backend response.
const TIMEOUT_MS = 5_000;

/**
 * Sends a Socket.IO event and waits for its acknowledgement response.
 *
 * If the server does not respond before the timeout, it returns a standard
 * error object instead of leaving the frontend request unresolved.
 */
function emit<T extends SocketResponse>(event: string, data?: unknown): Promise<T> {
    return new Promise((resolve) => {
        socketService.connect().timeout(TIMEOUT_MS).emit(
            // Name of the Socket.IO event handled by the backend.
            event,

            // Send an empty object when the event does not need data.
            data ?? {},

            // Socket.IO acknowledgement callback.
            (error: Error | null, response?: T) => resolve(
                // Return a consistent error response if the request timed out
                // or the backend did not send a response.
                error || !response
                    ? { ok: false, reason: "El servidor no respondió." } as T
                    : response,
            ),
        );
    });
}

/**
 * Socket service for manual event operations.
 */
export const eventCreationService = {
    // Starts a manual event session and obtains the simulation time.
    beginManual: () => emit<SocketResponse>("manual-event:begin"),

    // Creates a new manual event.
    createManual: (data: ManualEventPayload) => emit<SocketResponse>("manual-event:create", data),

    // Starts automatic event generation.
    startGeneration: () => emit<SocketResponse>("generation:start"),

    // Sends a validated manual correction for an existing event.
    updateManual: (data: UpdateEventPayload) =>
        emit<UpdateEventResponse>("manual-event:update", data),
};