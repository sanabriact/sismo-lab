// ------------------------------------------------------------------
// U pd at eE ve nt Re sp on se
// ------------------------------------------------------------------

import type { SocketResponse } from "./SocketResponse";

export interface UpdateEventResponse extends SocketResponse {
    queued?: boolean;
    revision?: number;
}