import { socketService } from "./socketService";
import type { StructureAuditResponse } from "../../models/interfaces/realTime/StructureAudit";

const TIMEOUT_MS = 5_000;

class StructureAuditService {
    // Requests a structure audit; always resolves (never rejects)
    request(): Promise<StructureAuditResponse> {
        return new Promise((resolve) => {
            socketService.connect().timeout(TIMEOUT_MS).emit(
                "structure:audit",
                {},
                (
                    error: Error | null,
                    response?: StructureAuditResponse,
                ) => {
                    // Timeout or empty response: fall back to a failure result
                    if (error || !response) {
                        resolve({
                            ok: false,
                            reason: "no_scenario",
                        });
                        return;
                    }

                    resolve(response);
                },
            );
        });
    }
}

export const structureAuditService = new StructureAuditService();