export interface AssociationManager {
    R: number;
    W: number;
    candidates: Record<string, unknown>;
    selected_references: Record<string, unknown>;
}