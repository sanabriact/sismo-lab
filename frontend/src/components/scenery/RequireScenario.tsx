// ------------------------------------------------------------------
// R eq ui re Sc en ar io
// ------------------------------------------------------------------

import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useObservable } from "../../stores/useObservable";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import Loading from "../../pages/loading/Loading";

// Route guard: ensures scenario store has hydrated from store and a scenario is loaded before rendering children
const requireScenario = ({children}: { children: ReactNode}) => {
    const { hydrated, loaded } = useObservable(scenarioStore);
    // Hydrated: store has been restored; loaded: a scenario exists and is ready
    if (!hydrated) return <Loading />
    if (!loaded) return <Navigate to="/load-scenario" replace/>
    return <>{children}</>
};

export default requireScenario;