import type { ChangeEvent } from "react";
import { NavLink } from "react-router-dom";
import { useObservable } from "../../stores/useObservable";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import { scenarioService } from "../../services/scenario/ScenarioService";
import type { AIScenarioMode } from "../../models/types/scenario/aiScenarioMode";

const AI_SCENARIO_OPTIONS: { mode: AIScenarioMode, title: string, description: string }[] = [
    {
        mode: "empty",
        title: "Sin eventos",
        description: "Añade un escenario sin eventos activos."
    },
    {
        mode: "insertion",
        title: "Eventos por inserción",
        description: "Añade un escenario con eventos activos. Serán procesados uno a uno en ambos árboles AVL y BST."
    },
    {
        mode: "topology",
        title: "Eventos por topología",
        description: "Añade un escenario con eventos activos. Será primero validado el árbol y posteriormente se recupera su estructura."
    }
];

const LoadScenario = () => {
    const state = useObservable(scenarioStore);
    const validating = state.operation === "validating";

    const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        e.target.value = "";
        if (file) void scenarioService.loadFromFile(file);
    };

    return (
        <section className="mx-auto max-w-3xl space-y-8 p-8">
            <h1 className="text-3xl font-bold text-gray-900">Cargar escenario</h1>

            {validating && <p className="rounded-lg bg-blue-50 p-3 text-blue-700">Validando escenario…</p>}

            {state.operation === "succeeded" && (
                <div className="rounded-lg border border-emerald-300 bg-emerald-50 p-4 text-emerald-800">
                    <p className="font-semibold">{state.message}</p>
                    {state.summary && (
                        <p className="text-sm">{state.summary.stations} estaciones · {state.summary.events} eventos</p>
                    )}
                    <NavLink to="/events/visualize-trees" className="mt-2 inline-block text-sm underline">
                        Ir a visualizar los árboles
                    </NavLink>
                </div>
            )}

            {state.operation === "failed" && (
                <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-800">
                    <p className="font-semibold">{state.message}</p>
                    {state.issues.length > 0 && (
                        <ul className="mt-2 max-h-48 list-disc space-y-1 overflow-auto pl-5 text-sm">
                            {state.issues.map((issue, i) => <li key={i}>{issue}</li>)}
                        </ul>
                    )}
                </div>
            )}

            <div className="space-y-2">
                <h2 className="text-xl font-semibold">Manual</h2>
                <label className={`inline-block rounded-lg bg-[#04172f] px-4 py-2 text-white ${validating ? "opacity-50" : "cursor-pointer hover:opacity-90"}`}>
                    Elegir archivo JSON
                    <input type="file" accept=".json,application/json" className="sr-only" disabled={validating} onChange={onFileChange} />
                </label>
            </div>

            <div className="space-y-2">
                <h2 className="text-xl font-semibold">Con IA</h2>
                <div className="grid gap-3 md:grid-cols-3">
                    {AI_SCENARIO_OPTIONS.map(({ mode, title, description }) => (
                        <button
                            key={mode}
                            disabled={validating}
                            onClick={() => scenarioService.loadFromAI(mode)}
                            className="rounded-xl border border-gray-200 p-4 text-left hover:bg-gray-50 disabled:opacity-50"
                        >
                            <p className="font-semibold">{title}</p>
                            <p className="mt-1 text-sm text-gray-500">{description}</p>
                        </button>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default LoadScenario;