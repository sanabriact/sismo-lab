import { socketService } from "./socketService";

export interface ManualEventPayload {
    id: number;
    magnitude: number;
    depth: number;
    epicenter_x: number;
    epicenter_y: number;
    datetime: string;
    station: number;
}

interface SocketResponse {
    ok: boolean;
    reason?: string;
    minimumDatetime?: string;
}

const TIMEOUT_MS = 5_000;

function emit<T extends SocketResponse>(event: string, data?: unknown): Promise<T> {
    return new Promise((resolve) => {
        socketService.connect().timeout(TIMEOUT_MS).emit(
            event,
            data ?? {},
            (error: Error | null, response?: T) => resolve(
                error || !response ? { ok: false, reason: "El servidor no respondió." } as T : response,
            ),
        );
    });
}

export const eventCreationService = {
    beginManual: () => emit<SocketResponse>("manual-event:begin"),
    createManual: (data: ManualEventPayload) => emit<SocketResponse>("manual-event:create", data),
    startGeneration: () => emit<SocketResponse>("generation:start"),
};
