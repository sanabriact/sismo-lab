// ------------------------------------------------------------------
// M od eS et Re sp on se
// ------------------------------------------------------------------

import type { ExecutionMode } from "../../types/observatory/ExecutionMode";

export interface ModeSetResponse {
    ok: boolean;
    reason?: string;
    mode?: ExecutionMode;
}