import type { SeismicEvent } from "../tree/SeismicEvent";

export type QueryType =
    | "by_id"
    | "top_pending"
    | "magnitude_range"
    | "date_depth_range"
    | "expensive_access";

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
    events?: QueryEvent[];
    requested?: number;
    limit?: number;
    event_id?: number;
    candidates?: QueryEvent[];
    selected_reference?: QueryEvent | null;
    used_by?: QueryEvent[];
    window_hours?: number;
    distance_limit_km?: number;
}
