import { Observable } from "../Observable";
import type { ClockState } from "../../models/interfaces/realTime/ClockState";

export const clockStore = new Observable<ClockState>({
    currentTime: null,
    operation: "idle",
    message: null,
});
