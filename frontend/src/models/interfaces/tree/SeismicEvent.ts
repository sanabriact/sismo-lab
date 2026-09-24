import type { Station } from "../station/Station";
import type { AttentionStatus } from "../../types/Event/AttentionStatus";
import type { EventKey } from "../../types/Event/EventKey";
import type { EventStatus } from "../../types/Event/EventStatus";

export interface SeismicEvent {
    attention_status: AttentionStatus;
    datetime: string;
    depth: number;
    epicenter_x: number;
    epicenter_y: number;
    event_status: EventStatus;
    expensive_acces: boolean;
    key: EventKey;
    populated_zone: boolean;
    reporting_stations: Station[];
    revision: number;
}