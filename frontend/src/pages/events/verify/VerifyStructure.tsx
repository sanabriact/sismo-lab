// ------------------------------------------------------------------
// V er if yS tr uc tu re
// ------------------------------------------------------------------

import { useEffect, useState } from "react";
import { structureAuditService } from "../../../services/socket/structureAuditService";
import type { StructureAuditReport } from "../../../models/interfaces/realTime/StructureAudit";

const VerifyStructure = () => {
    const [report, setReport] = useState<StructureAuditReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const verifyStructure = async () => {
        setLoading(true);
        setError(null);

        const response = await structureAuditService.request();

        if (!response.ok || !response.report) {
            setReport(null);
            setError("No fue posible verificar la estructura.");
            setLoading(false);
            return;
        }

        setReport(response.report);
        setLoading(false);
    };

    useEffect(() => {
        verifyStructure();
    }, []);

    if (loading) {
        return <section className="p-8">Verificando estructura…</section>;
    }

    if (error) {
        return (
            <section className="p-8 space-y-4">
                <p className="text-red-700">{error}</p>
                <button
                    type="button"
                    onClick={verifyStructure}
                    className="rounded bg-[#04172f] px-4 py-2 text-white"
                >
                    Reintentar
                </button>
            </section>
        );
    }

    if (!report) {
        return null;
    }

    const { audit, indicators, mode } = report;
    const counters = indicators.counters;

    return (
        <section className="space-y-8 p-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">
                        Verificar estructura
                    </h1>
                    <p className="mt-1 text-gray-600">
                        Modo actual: {mode === "normal" ? "Normal" : "Estrés"}
                    </p>
                </div>

                <button
                    type="button"
                    onClick={verifyStructure}
                    className="rounded bg-[#04172f] px-4 py-2 font-medium text-white"
                >
                    Verificar nuevamente
                </button>
            </div>

            <div
                className={
                    audit.ok
                        ? "rounded-lg border border-green-300 bg-green-50 p-4 text-green-800"
                        : "rounded-lg border border-red-300 bg-red-50 p-4 text-red-800"
                }
            >
                {audit.ok
                    ? "La estructura no presenta errores."
                    : "Se encontraron inconsistencias estructurales."}
                <p className="mt-1 text-sm">
                    Desbalance máximo: {audit.max_imbalance}
                </p>
                <p className="mt-1 text-sm">
                    Estado AVL: {audit.balanced ? "Balanceado" : "Desbalanceado"}
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <Indicator title="Eventos activos" value={indicators.tree.active_events} />
                <Indicator title="Eventos históricos" value={counters.historical_events} />
                <Indicator title="Altura del AVL" value={indicators.tree.height} />
                <Indicator title="Hojas" value={indicators.tree.leaves} />
                <Indicator title="Pendientes" value={counters.pending_attention} />
                <Indicator title="Acceso costoso" value={counters.high_cost_access_events} />
            </div>

            <section className="rounded-lg border border-gray-200 p-5">
                <h2 className="text-xl font-semibold">Recorridos</h2>
                <Traversal title="Preorden" values={indicators.tree.preorder} />
                <Traversal title="Inorden" values={indicators.tree.inorder} />
                <Traversal title="Postorden" values={indicators.tree.postorder} />
                <Traversal title="Por niveles" values={indicators.tree.levels} />
            </section>

            <section className="rounded-lg border border-gray-200 p-5">
                <h2 className="text-xl font-semibold">Contadores AVL</h2>
                <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <Indicator title="Casos LL" value={counters.ll_cases} />
                    <Indicator title="Casos RR" value={counters.rr_cases} />
                    <Indicator title="Casos LR" value={counters.lr_cases} />
                    <Indicator title="Casos RL" value={counters.rl_cases} />
                    <Indicator title="Giros izquierdos" value={counters.simple_left_rotations} />
                    <Indicator title="Giros derechos" value={counters.simple_right_rotations} />
                </div>
            </section>

            <section className="rounded-lg border border-gray-200 p-5">
                <h2 className="text-xl font-semibold">Eventos por prioridad</h2>
                <div className="mt-4 grid gap-4 sm:grid-cols-3">
                    <Indicator title="Prioridad 1" value={counters.events_by_priority[1] ?? 0} />
                    <Indicator title="Prioridad 2" value={counters.events_by_priority[2] ?? 0} />
                    <Indicator title="Prioridad 3" value={counters.events_by_priority[3] ?? 0} />
                </div>
            </section>

            {audit.warnings.length > 0 && (
                <IssueList
                    title="Desbalances esperados"
                    items={audit.warnings}
                    colorClass="border-amber-300 bg-amber-50 text-amber-900"
                />
            )}

            {audit.issues.length > 0 && (
                <IssueList
                    title="Inconsistencias detectadas"
                    items={audit.issues}
                    colorClass="border-red-300 bg-red-50 text-red-900"
                />
            )}
        </section>
    );
};

const Indicator = ({ title, value }: { title: string; value: number }) => {
    return (
        <article className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-500">{title}</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
        </article>
    );
};

const Traversal = ({ title, values }: { title: string; values: number[] }) => {
    return (
        <p className="mt-3 text-sm text-gray-700">
            <span className="font-semibold">{title}: </span>
            {values.length === 0 ? "Árbol vacío" : values.join(" → ")}
        </p>
    );
};

const IssueList = ({
    title,
    items,
    colorClass,
}: {
    title: string;
    items: { id: number | null; type: string; message: string }[];
    colorClass: string;
}) => {
    return (
        <section className={`rounded-lg border p-5 ${colorClass}`}>
            <h2 className="text-xl font-semibold">{title}</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
                {items.map((item, index) => (
                    <li key={`${item.type}-${item.id}-${index}`}>
                        {item.id !== null ? `Evento ${item.id}: ` : ""}
                        {item.message}
                    </li>
                ))}
            </ul>
        </section>
    );
};

export default VerifyStructure;