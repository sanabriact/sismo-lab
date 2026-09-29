import type { ScenarioLoadedPayload } from "../../models/interfaces/scenery/ScenarioLoadedPayload";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import type { ScenarioStatusResponse } from "../../models/interfaces/scenery/ScenarioStatusResponse";
import type { ScenarioSource } from "../../models/types/scenario/ScenarioSource";

export function applyScenarioPending(source: ScenarioSource): void {
    const current = scenarioStore.getSnapshot();
    scenarioStore.set({
        ...current,
        operation: "validating",
        source,
        message: null,
        issues: []
    });
}

export function applyScenarioPayload(payload: ScenarioLoadedPayload): void {
    const current = scenarioStore.getSnapshot();
    scenarioStore.set({
        ...current,
        hydrated: true,
        loaded: true,
        scenarioId: payload.scenarioId,
        operation: "succeeded",
        message: "Escenario cargado correctamente",
        issues: [],
        summary: {
            stations: payload.stations,
            events: payload.events
        }
    });
}

export function applyScenarioFailed(message: string, issues: string[] = []): void {
    const current = scenarioStore.getSnapshot();
    scenarioStore.set({
        ...current,
        operation: "failed",
        message,
        issues
    })
}

export function applyScenarioStatus(status: ScenarioStatusResponse | null): void {
    const current = scenarioStore.getSnapshot();
    if (current.operation === "validating") {
        scenarioStore.set({
            ...current,
            hydrated: true
        })
        return;
    }
    scenarioStore.set({
        ...current,
        hydrated: true,
        loaded: status?.loaded ?? false,
        scenarioId: status?.scenarioId ?? null
    });
}