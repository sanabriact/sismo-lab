import type { SeismicEvent } from "./SeismicEvent";

export interface Node {
    height: number;
    leftChild: Node | null;
    rightChild: Node | null;
    value: SeismicEvent;
    nodeCreationTime: string | null;
}