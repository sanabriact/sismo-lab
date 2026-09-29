import type { ScenarioOperation } from "../../types/scenario/ScenarioOperation";
import type { ScenarioSource } from "../../types/scenario/ScenarioSource";

export interface ScenarioState {
    hydrated: boolean;
    loaded: boolean;
    scenarioId: string | null;
    operation: ScenarioOperation;
    source: ScenarioSource | null;
    message: string | null;
    issues: string[];
    summary: {
        stations: number;
        events: number;
    } | null;
}