import type { Node } from "./Node";

export interface VIZNode {
    id: string;
    dto: Node | null;
    children?: VIZNode[];
}