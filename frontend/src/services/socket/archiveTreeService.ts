import { socketService } from "./socketService";
import type {
    ArchiveDecisionResponse,
    PrepareArchiveTreeResponse,
} from "../../models/interfaces/realTime/ArchiveTree";

const TIMEOUT_MS = 5_000;

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
    prepare: () => emit<PrepareArchiveTreeResponse>("paint:tree", {}),
    decide: (archive: boolean) => emit<ArchiveDecisionResponse>(
        "archive:decision",
        { archive },
    ),
};
