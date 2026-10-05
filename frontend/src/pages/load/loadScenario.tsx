// ------------------------------------------------------------------
// l oa dS ce na ri o
// ------------------------------------------------------------------

import type { ChangeEvent } from "react";
import { NavLink } from "react-router-dom";
import { useObservable } from "../../stores/useObservable";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import { scenarioService } from "../../services/scenario/ScenarioService";
import type { AIScenarioMode } from "../../models/types/scenario/aiScenarioMode";

// Scenario generation modes available for AI-based scenario creation
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

// Page for loading scenarios from JSON file or AI-generated with selected mode
const LoadScenario = () => {
    const state = useObservable(scenarioStore);
    const validating = state.operation === "validating";

    // Handles file input; extracts file and triggers load; resets input for re-selection
    const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        e.target.value = "";
        if (file) void scenarioService.loadFromFile(file);
    };

    // Triggers AI scenario generation with specified mode
    const onAIChange = (mode: AIScenarioMode) => {
        scenarioService.loadFromAI(mode);
    }

    return (
        <section className="mx-auto max-w-3xl space-y-8 p-8">
            <h1 className="text-3xl font-bold text-gray-900">Cargar escenario</h1>

            {/* Validation feedback */}
            {validating && <p className="rounded-lg bg-blue-50 p-3 text-blue-700">Validando escenario…</p>}

            {/* Success state: displays scenario summary and link to tree visualization */}
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

            {/* Error state: displays validation message and detailed error list */}
            {state.operation === "failed" && (
                <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-800">
                    <p className="font-semibold">{state.message}</p>
                    {state.issues.length > 0 && (
                        <div className="mt-4 overflow-hidden rounded-lg border border-red-200 bg-white text-sm text-gray-800">
                            <div className="bg-red-100 px-3 py-2 font-semibold text-red-900">
                                Errores encontrados ({state.issues.length})
                            </div>
                            <div className="grid grid-cols-[4rem_minmax(0,1fr)] border-t border-red-200 bg-red-50 px-3 py-2 font-semibold text-red-900">
                                <span>#</span>
                                <span>Detalle</span>
                            </div>
                            <div className="max-h-64 overflow-auto">
                                {state.issues.map((issue, i) => (
                                    <div key={`${i}-${issue}`} className="grid grid-cols-[4rem_minmax(0,1fr)] border-t border-red-100 px-3 py-2 odd:bg-white even:bg-red-50">
                                        <span className="text-gray-500">{i + 1}</span>
                                        <span className="wrap-break-words">{issue}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Manual scenario loading via JSON file upload */}
            <div className="space-y-2">
                <h2 className="text-xl font-semibold">Manual</h2>
                <label className={`inline-block rounded-lg bg-[#04172f] px-4 py-2 text-white ${validating ? "opacity-50" : "cursor-pointer hover:opacity-90"}`}>
                    Elegir archivo JSON
                    <input type="file" accept=".json,application/json" className="sr-only" disabled={validating} onChange={onFileChange} />
                </label>
            </div>

            {/* AI-generated scenario options: empty, insertion, or topology modes */}
            <div className="space-y-2">
                <h2 className="text-xl font-semibold">Con IA</h2>
                <div className="grid gap-3 md:grid-cols-3">
                    {AI_SCENARIO_OPTIONS.map(({ mode, title, description }) => (
                        <button
                            key={mode}
                            disabled={validating}
                            onClick={() => onAIChange(mode)}
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