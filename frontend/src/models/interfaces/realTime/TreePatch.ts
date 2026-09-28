import type { RealTimeNode } from "./RealtimeNode";

export interface TreePatch {
    upserted: RealTimeNode[];   
    removedIds: number[];  
    rootId: number | null; 
}