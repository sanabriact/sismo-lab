import { useMemo } from "react";
import { hierarchy, tree } from "d3-hierarchy";
import type { HierarchyPointLink, HierarchyPointNode } from "d3-hierarchy";
import { linkVertical } from "d3-shape";
import type { TreeViewProps } from "../../models/interfaces/tree/TreeViewProps";
import type { VIZNode } from "../../models/interfaces/tree/VIZNode";
import { toVIZ } from "../../utils/viznode/toHierarchy";

/* 
    node_w its the width space designed for each node.
    node_h is the height space designed for each node.
    r its the node circle radius.
    Each of them are in pixels units.
*/
const NODE_W = 100;
const NODE_H = 90;
const R = 25;
const CHARACTERISTICS_W = 122;

/* 
    Here we generate the lines that connects each node.
    D3 receives a connection betweeen parent and one children and generates the "d" attribute for a SVG. (Attribute for 
    defining trayectories o drawing commands for geometric shapes.)
    
*/
const linesGenerator = linkVertical<HierarchyPointLink<VIZNode>, HierarchyPointNode<VIZNode>>().x((d) => d.x).y((d) => d.y);

/* 
    Here we define the props that the component need to renderize at its full (data).
*/
export function TreeView({ data, type, highlightIds, showCharacteristics = false, characteristics }: TreeViewProps) {
    /* 
        Here is the base of all the component.
    */
    const layout = useMemo(() => {
        /* First checks if root exists. */
        if (!data.root) return null;
        /* 
            First, toVIZ is a function located in utils that helps us to transform the root node to a VIZNode type.
            Example: from atributes id, value, left_child, right_child => transforms into id, dto and children.

            Then hierarchy function takes this tree and constructs a jerarquic representation. (Like the visual view of the tree).
            And for finishing, tree<VIZNode>() generates the tree layout and each node has a width and height depending on the value we want. We can change it from NODE_W and NODE_H constants up.
        */
        const horizontalSpacing = NODE_W + (showCharacteristics ? CHARACTERISTICS_W : 0);
        return tree<VIZNode>().nodeSize([horizontalSpacing, NODE_H])(hierarchy(toVIZ(data.root)));

        /* 
            And the last thing of this function, is the use of useMemo for React to remember and save the tree layout, so when data doesn't changes (observatory doesn't change neither), React reutilize the tree layout saved in this variable-function.
        */
    }, [data, showCharacteristics])

    /* 
        If there's no layout, we return a simple message indicating that tree doesn't have values.
    */
    if (!layout) return <p className="text-gray-500">Árbol Vacío</p>

    /* 
        Here we define various things:
        1. We define the list of nodes with the method ".descendants" and filter the only list of nodes that have "dto" property. 
        2. We define the list of lines or links (parent -> child), and filter the only list of links that it's target have "dto" property.
        3. We define the horizontal size of the tree, generating a new list with all the values of X of each node.
        4. We define the minimum value of X for spacing terms, transversing the previous list of X values and subtracting with the NODE_W defined before for more space.
        5. We calculate the width that will contain all the tree depending of the nodes positions. (Because each node has X, Y coordinates)
        6. We calculate the height depending on the tree real hight (using the tree's levels) and the NODE_H value.
    
    */
    const nodes = layout.descendants().filter((n) => n.data.dto);
    const links = layout.links().filter((l) => l.target.data.dto);
    const xs = layout.descendants().map((n) => n.x);
    const minX = Math.min(...xs) - NODE_W / 2;
    const width = Math.max(...xs) - minX + NODE_W / 2 + (showCharacteristics ? CHARACTERISTICS_W : 0);
    const height = (layout.height + 1) * NODE_H;

    return (
        /* 
            Here we start constructing the SVG (tree) 
            viewBox defines the SVG intern coordinates system. (startX startY widht height)
            We use -R*2 for having more space up of the tree.
        */
        <svg viewBox={`${minX} ${-R * 2} ${width} ${height}`} width={width} height={height}>
            {/* 
                Here we renderize each line or link betweeen nodes, using our helper function "linesGenerator":
                The <path> tag it's used for generate a SVG line for each link mapping.
                Remember that the "d" attribute its used for generate the geometrical shape of each connection.
            */}
            {links.map((l) => (
                <path key={l.target.data.id} d={linesGenerator(l) ?? ""} fill="none" stroke="#888" />
            ))}
            {/* 
                Then we renderize each node.
            */}
            {nodes.map((n) => {
                /* 
                    For each node, we generate various things:
                    1. dto constant 
                    2. balance factor of the node; it asks if the node has left or right child.
                        If its true, then get it's equivalent height. If not true, then it returns undefined.
                        Then, if the result is null or undefined, the height will be -1.
                    3. A <g> tag that represents the SVG group.
                    4. A "transform" attribute that contains a "translate" based on the node X and Y coordinate.
                        For example if a node have n.x = 80 and n.y = 120, React will move the node to that coordinates.
                    5. A <circle> tag that will contain the radius, inside color white and border color approximately to a black.
                    6. Two <text> tags: 
                        The first one will show the value of the node (key = [priority, magnitude, id]) inside the circle. The ".join" will generate these values separated with commas. "textAnchor" and "dy" will put this value on the center inside the circle.

                        The second one, will show the balance factor of each node, calculated with its formula. 
                 */
                const dto = n.data.dto!;
                const isArchiveCandidate = highlightIds?.has(dto.value.key[2]) ?? false;
                const nodeCharacteristics = characteristics?.[String(dto.value.key[2])];
                return (
                    <g key={n.data.id} transform={`translate(${n.x},${n.y})`}>
                        <circle
                            r={R}
                            fill={isArchiveCandidate ? "#fde68a" : "#fff"}
                            stroke={isArchiveCandidate ? "#d97706" : "#333"}
                            strokeWidth={isArchiveCandidate ? 3 : 1}
                        />
                        <text textAnchor="middle" dy=".3em" fontSize={10}>
                            {dto.value.key.join(" , ")}
                        </text>
                        {type === "avl" ? (
                            <text textAnchor="middle" y={R + 14} fontSize={10} fill="#666">
                                BF {(dto.left_child?.height ?? -1) - (dto.right_child?.height ?? -1)}
                            </text>
                        ) :
                        (
                            <></>
                        )
                        }
                        {showCharacteristics && nodeCharacteristics && (
                            <g aria-label={`Altura ${nodeCharacteristics.height}, profundidad ${nodeCharacteristics.depth}, prioridad ${nodeCharacteristics.priority}, acceso costoso ${nodeCharacteristics.expensive_access ? "sí" : "no"}`}>
                                <rect x={R + 5} y={-17} width={CHARACTERISTICS_W - 10} height={43} rx={6} fill="#fff" stroke="#cbd5e1" />
                                <text x={R + 10} y={-5} fontSize={8} fill="#334155">Altura {nodeCharacteristics.height} · Prof. {nodeCharacteristics.depth}</text>
                                <text x={R + 10} y={7} fontSize={8} fill={nodeCharacteristics.priority === 3 ? "#9f1239" : "#334155"} fontWeight={nodeCharacteristics.priority === 3 ? 700 : 400}>
                                    Prioridad {nodeCharacteristics.priority}{nodeCharacteristics.priority === 3 ? " ★" : ""}
                                </text>
                                <text x={R + 10} y={19} fontSize={8} fill={nodeCharacteristics.expensive_access ? "#b91c1c" : "#475569"} fontWeight={nodeCharacteristics.expensive_access ? 700 : 400}>
                                    Costoso: {nodeCharacteristics.expensive_access ? "Sí" : "No"}
                                </text>
                            </g>
                        )}
                    </g>
                );
            })}
        </svg>
    );
};   
