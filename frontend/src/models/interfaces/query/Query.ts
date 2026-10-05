import type { SeismicEvent } from "../tree/SeismicEvent";

export type QueryType =
    | "by_id"
    | "top_pending"
    | "magnitude_range"
    | "date_depth_range"
    | "expensive_access"
    | "tree_comparison";

export interface QueryRequest {
    type: QueryType;
    parameters: Record<string, number | string>;
}

export interface QueryEvent extends SeismicEvent {
    event_id: number;
    priority: number;
    magnitude: number;
    node_depth: number | null;
    balance_factor: number | null;
}

export interface QueryResponse {
    ok: boolean;
    reason?: string;
    examined_nodes?: number;
    status?: "active" | "archived" | "deleted" | "not_found";
    event?: QueryEvent | null;
    events?: QueryEvent[] | ExpensiveAccessItem[];
    requested?: number;
    limit?: number;
    event_id?: number;
    candidates?: QueryEvent[];
    selected_reference?: QueryEvent | null;
    used_by?: QueryEvent[];
    window_hours?: number;
    distance_limit_km?: number;
    comparison?: {
        event_count: number;
        comparison_definition: string;
        runs: TreeComparisonRun[];
    };
}

export interface TreeComparisonRun {
    order:
        | "current_order"
        | "ascending_key"
        | "descending_key"
        | "ascending_id"
        | "descending_id"
        | "ascending_magnitude"
        | "descending_magnitude";
    event_count: number;
    searches_per_tree: number;
    avl: TreeComparisonMetrics;
    bst: TreeComparisonMetrics;
}

export interface ExpensiveAccessItem {
    event: QueryEvent;
    depth: number;
    limit: number;
    nodes_visited: number;
}

export interface TreeComparisonMetrics {
    root_id: number | null;
    height: number;
    leaves: number;
    search_comparisons: number;
    average_comparisons: number;
}
