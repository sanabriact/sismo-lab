import type { SeismicEvent } from "../tree/SeismicEvent";
import type { TreeStep } from "./TreeStep";

export interface TreeOperation {
    scenarioId: string;
    sequence: number;
    mode: "normal" | "stress";
    stationId: number;
    event: SeismicEvent;
    steps: TreeStep[]
}