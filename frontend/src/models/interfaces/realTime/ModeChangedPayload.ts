// ------------------------------------------------------------------
// M od eC ha ng ed Pa yl oa d
// ------------------------------------------------------------------

import type { ExecutionMode } from "../../types/observatory/ExecutionMode";

export interface ModeChangedPayload {
    mode: ExecutionMode;
    status: "changed" | "recovering" | "failed";
    balanced: boolean;
    maxImbalance: number;
    rotations: number;
    issues: unknown[]
}