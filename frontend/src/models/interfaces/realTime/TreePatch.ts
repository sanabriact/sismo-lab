import type { FlatNode } from "./FlatNode";

export interface TreePatch {
    operation: "inserted" | "rotation";
    upserted: FlatNode[];   
    removedIds: number[];  
    rootId: number | null; 
}