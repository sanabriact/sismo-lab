import type { Node } from "../../models/interfaces/tree/Node";
import type { VIZNode } from "../../models/interfaces/tree/VIZNode";

/* 
    Here we define a short util function called toVIZ. Basically, this help us to transform a backend response Node into a VIZNode.
    First, this function will return a VIZNode and will receive a node.
*/
export function toVIZ(node: Node | null, path = "root"): VIZNode {
    /* If Node is null, we return a VIZNode with id equaling root. */
    if(!node) return { id: path, dto: null};

    /* We create a constant called hasChildren for determining if the Node sent has children. */
    const hasChildren = node.left_child !== null || node.right_child !== null;
    /* We create the VIZNode form. */
    return {
        /* We get the key ( [priority, magnitude, id] )*/
        id: node.value.key.join("-"),
        /* dto refers to the original node data */
        dto: node,
        /* 
            if the node has children, then we create a list with [left_child, right_child] callingg recursively the function toVIZ
        */
        children: hasChildren ? [toVIZ(node.left_child, path + "L"), toVIZ(node.right_child, path + "R")] : undefined
    };
}