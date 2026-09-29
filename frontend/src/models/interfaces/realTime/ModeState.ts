import type { ExecutionMode } from "../../types/observatory/ExecutionMode";

export interface ModeState {
    mode: ExecutionMode;
    status: "idle" | "pending" | "recovering" | "failed";
    balanced: boolean;
    maxImbalance: number;
    reason: string | null;
}