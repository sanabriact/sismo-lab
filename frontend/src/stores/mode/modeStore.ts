import type { ModeState } from "../../models/interfaces/realTime/ModeState";
import { Observable } from "../Observable";

// Global execution mode state: mode, request status, tree balance info and error reason
export const modeStore = new Observable<ModeState>({
    mode: "normal",
    status: "idle",
    balanced: true,
    maxImbalance: 0,
    reason: null
});