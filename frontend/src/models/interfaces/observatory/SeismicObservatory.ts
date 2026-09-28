import type { AssociationManager } from "../../AssociationManager";
import type { Tree } from "../tree/Tree";

export interface SeismicObservatory {
    action_stack: { items: unknown[]};
    association_manager: AssociationManager;
    avl_tree: Tree;
    bst_tree: Tree;
}