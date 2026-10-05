// ------------------------------------------------------------------
// a rc hi ve Tr ee Se rv ic e
// ------------------------------------------------------------------

import { socketService } from "./socketService";
import type {
    ArchiveDecisionResponse,
    PrepareArchiveTreeResponse,
} from "../../models/interfaces/realTime/ArchiveTree";

const TIMEOUT_MS = 5_000;

// Emits a socket event; resolves null on timeout or empty response
function emit<T>(event: string, payload: unknown): Promise<T | null> {
    return new Promise((resolve) => {
        socketService.connect().timeout(TIMEOUT_MS).emit(
            event,
            payload,
            (error: Error | null, response?: T) => resolve(
                error || !response ? null : response,
            ),
        );
    });
}

export const archiveTreeService = {
    // Asks the server to prepare the tree for archiving
    prepare: () => emit<PrepareArchiveTreeResponse>("paint:tree", {}),
    // Sends the user's decision on whether to archive
    decide: (archive: boolean) => emit<ArchiveDecisionResponse>(
        "archive:decision",
        { archive },
    ),
};