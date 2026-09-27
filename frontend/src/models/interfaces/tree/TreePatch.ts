import type { FlatNode } from "./FlatNode";

export interface TreePatch {
    operation: "insert" | "delete" | "correct" | "rotate" | "archive" | "mark_reviewed" | "undo";
    upserted: FlatNode[];   
    removedIds: number[];  
    rootId: number | null; 
}