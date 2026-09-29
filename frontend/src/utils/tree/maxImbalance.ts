import type { Node } from "../../models/interfaces/tree/Node";

export function maxImbalance(node: Node | null): number {
    if(!node) return 0;
    const left = node.left_child?.height ?? - 1;
    const right = node.right_child?.height ?? -1;
    return Math.max(
        Math.abs(left - right),
        maxImbalance(node.left_child),
        maxImbalance(node.right_child)
    );
}