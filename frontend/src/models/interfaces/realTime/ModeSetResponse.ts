import type { ExecutionMode } from "../../types/observatory/ExecutionMode";

export interface ModeSetResponse {
    ok: boolean;
    reason?: string;
    mode?: ExecutionMode;
}