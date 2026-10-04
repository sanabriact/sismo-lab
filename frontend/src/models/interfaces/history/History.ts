import type { SeismicEvent } from "../tree/SeismicEvent";

export interface ArchivedEvent extends SeismicEvent {
    event_id: number;
    priority: number;
    magnitude: number;
}

export interface HistorySummary {
    ok: boolean;
    reason?: string;
    archived_events?: number;
    deleted_events?: number;
    historical_ids?: number;
}

export interface ArchivedEventsResponse {
    ok: boolean;
    reason?: string;
    events?: ArchivedEvent[];
    count?: number;
}

export interface DeletedEventsResponse {
    ok: boolean;
    reason?: string;
    events?: ArchivedEvent[];
    count?: number;
}

export interface HistoricalIdsResponse {
    ok: boolean;
    reason?: string;
    identifiers?: number[];
    count?: number;
}
