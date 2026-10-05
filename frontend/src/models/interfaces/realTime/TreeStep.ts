// ------------------------------------------------------------------
// T re eS te p
// ------------------------------------------------------------------

import type { Rotation } from "./Rotation";
import type { TreePatch } from "./TreePatch";

export interface TreeStep {
    kind: "insert" | "rotation" | "recovery-complete";
    avlPatch: TreePatch;
    bstPatch?: TreePatch;
    rotation?: Rotation;
}