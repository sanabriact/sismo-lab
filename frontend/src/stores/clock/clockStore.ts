import { Observable } from "../Observable";
import type { ClockState } from "../../models/interfaces/realTime/ClockState";

// Global clock state: current time, request status and error message
export const clockStore = new Observable<ClockState>({
    currentTime: null,
    operation: "idle",
    message: null,
});