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
    trees?: {
        avl: Record<string, NodeCharacteristics>;
        bst: Record<string, NodeCharacteristics>;
    };
}
