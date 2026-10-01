import type { Node } from "../../models/interfaces/tree/Node";

export function maxImbalance(node: Node | null): number {
    if(!node) return 0;
    // Recompute subtree heights from topology instead of trusting serialized
    // node metadata, which may be stale after a structural update.
    const leftHeight = subtreeHeight(node.left_child);
    const rightHeight = subtreeHeight(node.right_child);
    return Math.max(
        Math.abs(leftHeight - rightHeight),
        maxImbalance(node.left_child),
        maxImbalance(node.right_child)
    );
}

function subtreeHeight(node: Node | null): number {
    if (!node) return -1;
    return 1 + Math.max(subtreeHeight(node.left_child), subtreeHeight(node.right_child));
}
