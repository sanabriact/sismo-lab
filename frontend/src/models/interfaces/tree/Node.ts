import type { SeismicEvent } from "./SeismicEvent";

export interface Node {
    height: number;
    left_child: Node | null;
    right_child: Node | null;
    value: SeismicEvent;
    nodeCreationTime: string | null;
}