import { useSyncExternalStore } from "react";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";

// Hook that subscribes to scenario store and returns whether a scenario is loaded
export function useScenarioLoaded(): boolean {
    return useSyncExternalStore(scenarioStore.subscribe, () => scenarioStore.getSnapshot().loaded);
}