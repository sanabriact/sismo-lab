import type { TreePatch } from "../../models/interfaces/realTime/TreePatch";
import type { Tree } from "../../models/interfaces/tree/Tree";
import type { Node } from "../../models/interfaces/tree/Node";
import type { SeismicEvent } from "../../models/interfaces/tree/SeismicEvent";

// Indexes every node by event id (recursive traversal)
function indexNodes(node: Node | null, index: Map<number, Node>): void {
    if (!node) return;
    index.set(node.value.key[2], node);
    indexNodes(node.left_child, index);
    indexNodes(node.right_child, index);
}

/* Rebuilds the local hierarchy from an incremental server patch. */
export function applyTreePatch(tree: Tree, patch: TreePatch, insertedEvent: SeismicEvent | null): Tree {
    // Index the current tree by id
    const previous = new Map<number, Node>();
    indexNodes(tree.root, previous);
    const flat = new Map<number, {
        id: number;
        key: SeismicEvent["key"];
        height: number;
        leftChildId: number | null;
        rightChildId: number | null;
    }>();

    // Flatten the current tree into id-based entries
    previous.forEach((node, id) => flat.set(id, {
        id,
        key: node.value.key,
        height: node.height,
        leftChildId: node.left_child?.value.key[2] ?? null,
        rightChildId: node.right_child?.value.key[2] ?? null,
    }));
    // Apply the patch: remove deleted nodes, then add or replace upserted ones
    patch.removedIds.forEach((id) => flat.delete(id));
    patch.upserted.forEach((node) => flat.set(node.id, node));

    // Recursively rebuilds a node and its children from the flat map
    const makeNode = (id: number | null): Node | null => {
        if (id === null) return null;
        const item = flat.get(id);
        if (!item) return null;
        const old = previous.get(id);
        // Reuse the old event, use the inserted one, or fall back to a key-only stub
        const value = old?.value ?? (insertedEvent?.key[2] === id ? insertedEvent : { key: item.key } as SeismicEvent);
        return {
            height: item.height,
            value,
            left_child: makeNode(item.leftChildId),
            right_child: makeNode(item.rightChildId),
            nodeCreationTime: old?.nodeCreationTime ?? null,
        };
    };

    return { root: makeNode(patch.rootId) };
}