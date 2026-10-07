// ------------------------------------------------------------------
// S ce na ri oS ta te
// ------------------------------------------------------------------

import type { ScenarioOperation } from "../../types/scenario/ScenarioOperation";
import type { ScenarioSource } from "../../types/scenario/ScenarioSource";
import type { Zone } from "./Zone";
import type { Station } from "../station/Station";
import type { SeismicEvent } from "../tree/SeismicEvent";

export interface ScenarioVersion {
    version: number;
    saved_at?: string;
    snapshot: Record<string, unknown>;
}

export interface ScenarioState {
    hydrated: boolean;
    loaded: boolean;
    scenarioId: string | null;
    operation: ScenarioOperation;
    source: ScenarioSource | null;
    message: string | null;
    issues: string[];
    zones: Zone[];
    stations: Station[];
    events: SeismicEvent[];
    summary: {
        stations: number;
        events: number;
    } | null;
    versions: ScenarioVersion[];
    versionBaseline: Record<string, unknown> | null;
}
