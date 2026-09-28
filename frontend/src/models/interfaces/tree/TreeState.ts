import type { FlatNode } from "./FlatNode";

export interface TreeState {
    rootId: number | null;
    nodesById: Record<number, FlatNode>;
}