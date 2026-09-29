import type { TreePatch } from "../../models/interfaces/realTime/TreePatch";
import type { TreeState } from "../../models/interfaces/tree/TreeState";

export function applyPatch(state: TreeState, patch: TreePatch): TreeState {
    const nodesById = { ...state.nodesById };

    for (const node of patch.upserted){
        nodesById[node.id] = node;
    }
    for (const id of patch.removedIds) {
        delete nodesById[id];
    }
    
    return { rootId: patch.rootId , nodesById };
}