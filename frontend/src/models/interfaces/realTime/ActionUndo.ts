// ------------------------------------------------------------------
// A ct io nU nd o
// ------------------------------------------------------------------

export interface ActionUndonePayload {
    scenarioId: string | null;
    actionType: string;
    currentTime: string;
    events: number;
    remaining: number;
}

export interface ActionUndoResponse {
    ok: boolean;
    reason?: string;
    action?: {
        action_type: string;
    };
    snapshot?: ActionUndonePayload;
}
