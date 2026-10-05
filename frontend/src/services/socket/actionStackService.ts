// ------------------------------------------------------------------
// a ct io nS ta ck Se rv ic e
// ------------------------------------------------------------------

import { socketService } from "./socketService";
import { ObservatoryService } from "../seismicObservatory/seismicObservatoryService";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import { clockService } from "./clockService";
import { applySnapshot } from "../../utils/mode/ApplySnapshot";
import { maxImbalance } from "../../utils/tree/maxImbalance";
import type {
    ActionUndonePayload,
    ActionUndoResponse,
} from "../../models/interfaces/realTime/ActionUndo";
import type { SeismicObservatory } from "../../models/interfaces/observatory/SeismicObservatory";
import type { Node } from "../../models/interfaces/tree/Node";
import type { SeismicEvent } from "../../models/interfaces/tree/SeismicEvent";

const TIMEOUT_MS = 3_000;

const REASONS: Record<string, string> = {
    no_scenario: "Carga un escenario primero.",
    busy: "El escenario está ocupado recuperando su estructura.",
};

class ActionStackService {
    private readonly updateListeners = new Set<(payload: ActionUndonePayload) => void>();
    private updatesSubscribed = false;

    undo(): Promise<ActionUndoResponse> {
        return new Promise((resolve) => {
            socketService.connect().timeout(TIMEOUT_MS).emit(
                "action:undo",
                {},
                (error: Error | null, response?: ActionUndoResponse) => {
                    if (error || !response) {
                        resolve({ ok: false, reason: "El servidor no respondió." });
                        return;
                    }
                    resolve({
                        ...response,
                        reason: response.reason
                            ? REASONS[response.reason] ?? response.reason
                            : undefined,
                    });
                },
            );
        });
    }

    subscribeToUpdates(listener?: (payload: ActionUndonePayload) => void): () => void {
        const socket = socketService.connect();
        if (listener) this.updateListeners.add(listener);

        if (!this.updatesSubscribed) {
            this.updatesSubscribed = true;
            socket.on("action:undone", (payload: ActionUndonePayload) => {
                void this.handleUpdate(payload);
            });
        }

        return () => {
            if (listener) this.updateListeners.delete(listener);
        };
    }

    private async handleUpdate(payload: ActionUndonePayload): Promise<void> {
        await this.refreshFromApi(payload);
        this.updateListeners.forEach((listener) => listener(payload));
    }

    private async refreshFromApi(payload: ActionUndonePayload): Promise<void> {
        const observatory = await ObservatoryService.getObservatory();
        if (payload.actionType === "LOAD_SCENARIO" && payload.scenarioId === null) {
            this.clearScenario();
            return;
        }
        if (!observatory || observatory.scenario_id !== payload.scenarioId) return;

        this.applyObservatory(observatory, payload);
    }

    private clearScenario(): void {
        const current = scenarioStore.getSnapshot();
        scenarioStore.set({
            ...current,
            hydrated: true,
            loaded: false,
            scenarioId: null,
            operation: "idle",
            source: null,
            message: null,
            issues: [],
            zones: [],
            stations: [],
            events: [],
            summary: null,
        });
        clockService.setCurrentTime(null);
        applySnapshot("normal", 0);
    }

    private applyObservatory(
        observatory: SeismicObservatory,
        payload: ActionUndonePayload,
    ): void {
        const current = scenarioStore.getSnapshot();
        const events = this.eventsFromTree(observatory.avl_tree.root);

        if (current.scenarioId !== payload.scenarioId) return;

        scenarioStore.set({
            ...current,
            zones: observatory.zones,
            stations: observatory.stations,
            events,
            summary: {
                stations: observatory.stations.length,
                events: events.length,
            },
        });
        clockService.setCurrentTime(payload.currentTime);
        applySnapshot(
            observatory.execution_mode,
            maxImbalance(observatory.avl_tree.root),
        );
    }

    private eventsFromTree(node: Node | null): SeismicEvent[] {
        if (!node) return [];
        return [
            node.value,
            ...this.eventsFromTree(node.left_child),
            ...this.eventsFromTree(node.right_child),
        ];
    }
}

export const actionStackService = new ActionStackService();
