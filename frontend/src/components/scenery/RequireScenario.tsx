import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useObservable } from "../../stores/useObservable";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import Loading from "../../pages/loading/Loading";

const requireScenario = ({children}: { children: ReactNode}) => {
    const { hydrated, loaded } = useObservable(scenarioStore);
    if (!hydrated) return <Loading />
    if (!loaded) return <Navigate to="/load-scenario" replace/>
    return <>{children}</>
};

export default requireScenario;