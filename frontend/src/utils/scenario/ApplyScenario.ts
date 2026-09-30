import type { ScenarioLoadedPayload } from "../../models/interfaces/scenery/ScenarioLoadedPayload";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import type { ScenarioStatusResponse } from "../../models/interfaces/scenery/ScenarioStatusResponse";
import type { ScenarioSource } from "../../models/types/scenario/ScenarioSource";
import { ObservatoryService } from "../../services/seismicObservatory/seismicObservatoryService";
import type { TreeOperation } from "../../models/interfaces/realTime/TreeOperation";
import { toScenarioMap } from "./toScenarioMap";

async function hydrateScenarioMap(scenarioId: string): Promise<void> {
    const observatory = await ObservatoryService.getObservatory();
    const current = scenarioStore.getSnapshot();

    if (!observatory || observatory.scenario_id !== scenarioId || current.scenarioId !== scenarioId) return;

    scenarioStore.set({
        ...current,
        ...toScenarioMap(observatory),
    });
}

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

export async function applyScenarioPayload(payload: ScenarioLoadedPayload): Promise<void> {
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

    await hydrateScenarioMap(payload.scenarioId);
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

export async function applyScenarioStatus(status: ScenarioStatusResponse | null): Promise<void> {
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
        scenarioId: status?.scenarioId ?? null,
        zones: status?.loaded ? current.zones : [],
        stations: status?.loaded ? current.stations : [],
        events: status?.loaded ? current.events : [],
    });

    if (status?.loaded && status.scenarioId) {
        await hydrateScenarioMap(status.scenarioId);
    }
}

export function applyScenarioEvent(operation: TreeOperation): void {
    if (!operation.event) return;

    const current = scenarioStore.getSnapshot();
    if (current.scenarioId !== operation.scenarioId) return;

    const eventId = operation.event.key[2];
    scenarioStore.set({
        ...current,
        events: [
            ...current.events.filter((event) => event.key[2] !== eventId),
            operation.event,
        ],
    });
}
