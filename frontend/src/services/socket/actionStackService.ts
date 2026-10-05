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

// Backend error codes mapped to user-facing messages
const REASONS: Record<string, string> = {
    no_scenario: "Carga un escenario primero.",
    busy: "El escenario está ocupado recuperando su estructura.",
};

class ActionStackService {
    // External listeners notified after each undo update
    private readonly updateListeners = new Set<(payload: ActionUndonePayload) => void>();
    // Ensures the socket event is registered only once
    private updatesSubscribed = false;

    // Requests an undo; always resolves (never rejects)
    undo(): Promise<ActionUndoResponse> {
        return new Promise((resolve) => {
            socketService.connect().timeout(TIMEOUT_MS).emit(
                "action:undo",
                {},
                (error: Error | null, response?: ActionUndoResponse) => {
                    // Timeout or empty response
                    if (error || !response) {
                        resolve({ ok: false, reason: "El servidor no respondió." });
                        return;
                    }
                    // Translate known reason codes
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

    // Listens to undo updates; returns an unsubscribe function
    subscribeToUpdates(listener?: (payload: ActionUndonePayload) => void): () => void {
        const socket = socketService.connect();
        if (listener) this.updateListeners.add(listener);

        // Register the socket handler on first subscription only
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

    // Refreshes local state first, then notifies listeners
    private async handleUpdate(payload: ActionUndonePayload): Promise<void> {
        await this.refreshFromApi(payload);
        this.updateListeners.forEach((listener) => listener(payload));
    }

    // Fetches the observatory and syncs the store with it
    private async refreshFromApi(payload: ActionUndonePayload): Promise<void> {
        const observatory = await ObservatoryService.getObservatory();
        // Undoing the scenario load leaves no scenario
        if (payload.actionType === "LOAD_SCENARIO" && payload.scenarioId === null) {
            this.clearScenario();
            return;
        }
        // Ignore missing or mismatched observatory
        if (!observatory || observatory.scenario_id !== payload.scenarioId) return;

        this.applyObservatory(observatory, payload);
    }

    // Resets the store, clock and mode to the empty state
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

    // Applies observatory data to the store, clock and execution mode
    private applyObservatory(
        observatory: SeismicObservatory,
        payload: ActionUndonePayload,
    ): void {
        const current = scenarioStore.getSnapshot();
        const events = this.eventsFromTree(observatory.avl_tree.root);

        // Skip if the active scenario changed meanwhile
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
        // Mode plus the tree's max imbalance
        applySnapshot(
            observatory.execution_mode,
            maxImbalance(observatory.avl_tree.root),
        );
    }

    // Flattens the tree into an event list (pre-order traversal)
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