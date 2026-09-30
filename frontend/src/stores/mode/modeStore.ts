import type { ModeState } from "../../models/interfaces/realTime/ModeState";
import { Observable } from "../Observable";

export const modeStore = new Observable<ModeState>({
    mode: "normal",
    status: "idle",
    balanced: true,
    maxImbalance: 0,
    reason: null
});