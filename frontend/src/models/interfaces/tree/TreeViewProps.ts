import type { Tree } from "./Tree";

export interface TreeViewProps {
    data: Tree;
    type: "avl" | "bst";
}