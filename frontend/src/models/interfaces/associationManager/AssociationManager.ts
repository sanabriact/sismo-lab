// ------------------------------------------------------------------
// A ss oc ia ti on Ma na ge r
// ------------------------------------------------------------------

export interface AssociationManager {
    R: number;
    W: number;
    candidates: Record<string, unknown>;
    selected_references: Record<string, unknown>;
}