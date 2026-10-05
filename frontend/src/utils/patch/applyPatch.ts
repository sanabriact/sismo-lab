// ------------------------------------------------------------------
// a pp ly Pa tc h
// ------------------------------------------------------------------

import type { TreePatch } from "../../models/interfaces/realTime/TreePatch";
import type { TreeState } from "../../models/interfaces/tree/TreeState";

// Returns a new tree state with the patch applied (no mutation of the original)
export function applyPatch(state: TreeState, patch: TreePatch): TreeState {
    // Shallow copy so the previous state stays untouched
    const nodesById = { ...state.nodesById };

    // Add or replace nodes
    for (const node of patch.upserted){
        nodesById[node.id] = node;
    }
    // Remove deleted nodes
    for (const id of patch.removedIds) {
        delete nodesById[id];
    }
    
    return { rootId: patch.rootId , nodesById };
}