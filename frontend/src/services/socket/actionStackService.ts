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

    subscribeToUpdates(): () => void {
        const socket = socketService.connect();
        const handleUpdate = (payload: ActionUndonePayload) => {
            void this.refreshFromApi(payload);
        };

        socket.on("action:undone", handleUpdate);
        return () => socket.off("action:undone", handleUpdate);
    }

    private async refreshFromApi(payload: ActionUndonePayload): Promise<void> {
        const observatory = await ObservatoryService.getObservatory();
        if (!observatory || observatory.scenario_id !== payload.scenarioId) return;

        this.applyObservatory(observatory, payload);
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
