import { useSyncExternalStore } from "react";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";

export function useScenarioLoaded(): boolean {
    return useSyncExternalStore(scenarioStore.subscribe, () => scenarioStore.getSnapshot().loaded);
}