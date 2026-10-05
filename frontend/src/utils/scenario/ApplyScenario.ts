// ------------------------------------------------------------------
// A pp ly Sc en ar io
// ------------------------------------------------------------------

import type { ScenarioLoadedPayload } from "../../models/interfaces/scenery/ScenarioLoadedPayload";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import type { ScenarioStatusResponse } from "../../models/interfaces/scenery/ScenarioStatusResponse";
import type { ScenarioSource } from "../../models/types/scenario/ScenarioSource";
import { ObservatoryService } from "../../services/seismicObservatory/seismicObservatoryService";
import type { TreeOperation } from "../../models/interfaces/realTime/TreeOperation";
import { toScenarioMap } from "./toScenarioMap";
import { clockService } from "../../services/socket/clockService";

// Loads map data (zones, stations, events) into the store if the scenario is still current
async function hydrateScenarioMap(scenarioId: string): Promise<void> {
    const observatory = await ObservatoryService.getObservatory();
    const current = scenarioStore.getSnapshot();

    // Ignore stale responses (scenario changed while fetching)
    if (!observatory || observatory.scenario_id !== scenarioId || current.scenarioId !== scenarioId) return;

    scenarioStore.set({
        ...current,
        ...toScenarioMap(observatory),
    });
}

// Marks a scenario load as in progress
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

// Applies a successfully loaded scenario, syncs the clock and hydrates the map
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
    clockService.setCurrentTime(payload.currentTime);

    await hydrateScenarioMap(payload.scenarioId);
}

// Marks a scenario load as failed with a message and issue list
export function applyScenarioFailed(message: string, issues: string[] = []): void {
    const current = scenarioStore.getSnapshot();
    scenarioStore.set({
        ...current,
        operation: "failed",
        message,
        issues
    })
}

// Syncs the store with the server's scenario status (null = no response)
export async function applyScenarioStatus(status: ScenarioStatusResponse | null): Promise<void> {
    const current = scenarioStore.getSnapshot();
    // A load is in progress: only mark the store as hydrated
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
        // Keep map data only when a scenario is loaded
        zones: status?.loaded ? current.zones : [],
        stations: status?.loaded ? current.stations : [],
        events: status?.loaded ? current.events : [],
    });

    // Fetch the map data for the loaded scenario
    if (status?.loaded && status.scenarioId) {
        await hydrateScenarioMap(status.scenarioId);
    }
}

// Upserts an event from a tree operation (matched by event id)
export function applyScenarioEvent(operation: TreeOperation): void {
    if (!operation.event) return;

    // Ignore operations from another scenario
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