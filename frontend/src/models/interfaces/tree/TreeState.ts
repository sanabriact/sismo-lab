import type { FlatNode } from "../realTime/FlatNode";

export interface TreeState {
    rootId: number | null;
    nodesById: Record<number, FlatNode>;
}