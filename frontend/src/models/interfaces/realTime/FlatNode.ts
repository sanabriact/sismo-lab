import type { EventKey } from "../../types/event/EventKey";

export interface FlatNode {
    id: number;
    key: EventKey;
    height: number;
    leftChildId: number | null;
    rightChildId: number | null;
    parentId: number | null;
}