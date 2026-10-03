import type { SocketResponse } from "./SocketResponse";

export interface UpdateEventResponse extends SocketResponse {
    queued?: boolean;
    revision?: number;
}