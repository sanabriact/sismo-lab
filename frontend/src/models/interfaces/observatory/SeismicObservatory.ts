// ------------------------------------------------------------------
// S ei sm ic Ob se rv at or y
// ------------------------------------------------------------------

import type { ExecutionMode } from "../../types/observatory/ExecutionMode";
import type { AssociationManager } from "../associationManager/AssociationManager";
import type { Tree } from "../tree/Tree";
import type { Station } from "../station/Station";
import type { Zone } from "../scenery/Zone";

export interface SeismicObservatory {
    action_stack: { items: unknown[]};
    association_manager: AssociationManager;
    avl_tree: Tree;
    bst_tree: Tree;
    execution_mode: ExecutionMode;
    scenario_id: string | null;
    stations: Station[];
    zones: Zone[];
}
