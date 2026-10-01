import { socketService } from "./socketService";
import type { StructureAuditResponse } from "../../models/interfaces/realTime/StructureAudit";

const TIMEOUT_MS = 5_000;

class StructureAuditService {
    request(): Promise<StructureAuditResponse> {
        return new Promise((resolve) => {
            socketService.connect().timeout(TIMEOUT_MS).emit(
                "structure:audit",
                {},
                (
                    error: Error | null,
                    response?: StructureAuditResponse,
                ) => {
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