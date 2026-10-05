// ------------------------------------------------------------------
// R ot at io n
// ------------------------------------------------------------------

export interface Rotation {
    type: "LL" | "RR" | "LR" | "RL";
    pivotId: number;
    newRootId: number;
    affectedIds: number[];
}