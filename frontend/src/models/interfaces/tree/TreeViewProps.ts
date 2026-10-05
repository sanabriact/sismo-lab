import type { Tree } from "./Tree";
import type { NodeCharacteristics } from "./NodeCharacteristics";

export interface TreeViewProps {
    data: Tree;
    type: "avl" | "bst";
    highlightIds?: ReadonlySet<number>;
    showCharacteristics?: boolean;
    characteristics?: Record<string, NodeCharacteristics>;
}
