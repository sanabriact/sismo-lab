import type { QueryEvent } from "../query/Query";

export interface AssociationQueryResponse {
    ok: boolean;
    reason?: string;
    examined_nodes?: number;
    event_id?: number;
    candidates?: QueryEvent[];
    selected_reference?: QueryEvent | null;
    used_by?: QueryEvent[];
    window_hours?: number;
    distance_limit_km?: number;
}
