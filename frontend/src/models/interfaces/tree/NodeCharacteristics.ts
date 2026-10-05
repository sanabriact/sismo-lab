// ------------------------------------------------------------------
// N od eC ha ra ct er is ti cs
// ------------------------------------------------------------------

export interface NodeCharacteristics {
    height: number;
    depth: number;
    priority: number;
    expensive_access: boolean;
}

export interface TreeCharacteristicsResponse {
    ok: boolean;
    reason?: string;
    limit?: number;
    tree_summaries?: {
        avl: TreeSummary;
        bst: TreeSummary;
    };
    trees?: {
        avl: Record<string, NodeCharacteristics>;
        bst: Record<string, NodeCharacteristics>;
    };
}

export interface TreeSummary {
    root_id: number | null;
    height: number;
    max_depth: number;
    leaves: number;
}
