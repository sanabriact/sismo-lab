import type { TreePatch } from "../../models/interfaces/realTime/TreePatch";
import type { Tree } from "../../models/interfaces/tree/Tree";
import type { Node } from "../../models/interfaces/tree/Node";
import type { SeismicEvent } from "../../models/interfaces/tree/SeismicEvent";

function indexNodes(node: Node | null, index: Map<number, Node>): void {
    if (!node) return;
    index.set(node.value.key[2], node);
    indexNodes(node.left_child, index);
    indexNodes(node.right_child, index);
}

/** Reconstruye la jerarquía local desde un parche incremental del servidor. */
export function applyTreePatch(tree: Tree, patch: TreePatch, insertedEvent: SeismicEvent | null): Tree {
    const previous = new Map<number, Node>();
    indexNodes(tree.root, previous);
    const flat = new Map<number, {
        id: number;
        key: SeismicEvent["key"];
        height: number;
        leftChildId: number | null;
        rightChildId: number | null;
    }>();

    previous.forEach((node, id) => flat.set(id, {
        id,
        key: node.value.key,
        height: node.height,
        leftChildId: node.left_child?.value.key[2] ?? null,
        rightChildId: node.right_child?.value.key[2] ?? null,
    }));
    patch.removedIds.forEach((id) => flat.delete(id));
    patch.upserted.forEach((node) => flat.set(node.id, node));

    const makeNode = (id: number | null): Node | null => {
        if (id === null) return null;
        const item = flat.get(id);
        if (!item) return null;
        const old = previous.get(id);
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
