import type { SeismicEvent } from "../tree/SeismicEvent";

export interface RealTimeNode {
    id: number;
    event: SeismicEvent;
    leftId: number;
    rightId: number;
    heihgt: number;
}