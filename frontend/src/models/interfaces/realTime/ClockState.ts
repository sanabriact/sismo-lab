export type ClockOperation = "idle" | "pending" | "failed";

export interface ClockState {
    currentTime: string | null;
    operation: ClockOperation;
    message: string | null;
}
