import type { Station } from "./Station";

export interface SeismicEvent {
    attention_status: "pending" | "checked";
    datetime: string;
    depth: number;
    epicenter_x: number;
    epicenter_y: number;
    event_status: "active" | "archived" | "deleted";
    expensive_acces: boolean;
    key: [number, number, number];
    populated_zone: boolean;
    reporting_stations: Station[];
    revision: number;
}