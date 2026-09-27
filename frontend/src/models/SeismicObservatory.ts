import type { AssociationManager } from "./AssociationManager";
import type { Tree } from "./Tree";

export interface SeismicObservatory {
    action_stack: { items: unknown[]};
    association_manager: AssociationManager;
    avl: Tree;
}