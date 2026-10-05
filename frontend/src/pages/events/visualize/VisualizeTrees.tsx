import { useCallback, useEffect, useMemo, useState } from "react";
import { Info } from "lucide-react";
import { ObservatoryService } from "../../../services/seismicObservatory/seismicObservatoryService";
import type { SeismicObservatory } from "../../../models/interfaces/observatory/SeismicObservatory";
import { TreeView } from "../../../components/tree/TreeView";
import { ArchiveTreePanel } from "../../../components/tree/ArchiveTreePanel";
import { useObservatorySocket } from "../../../hooks/socket/useObservatorySocket";
import { applyTreePatch } from "../../../utils/tree/applyTreePatch";
import type { TreeOperation } from "../../../models/interfaces/realTime/TreeOperation";
import { actionStackService } from "../../../services/socket/actionStackService";
import { treeCharacteristicsService } from "../../../services/seismicObservatory/treeCharacteristicsService";
import type { TreeCharacteristicsResponse } from "../../../models/interfaces/tree/NodeCharacteristics";

// Page displaying AVL and BST trees with real-time updates, characteristics, and archive panel
const VisualizeTrees = () => {
    const [data, setData] = useState<SeismicObservatory | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [characteristics, setCharacteristics] = useState<TreeCharacteristicsResponse | null>(null);
    const [characteristicsLimit, setCharacteristicsLimit] = useState<number | null>(null);
    const [characteristicsError, setCharacteristicsError] = useState<string | null>(null);
    const [showCharacteristics, setShowCharacteristics] = useState(false);
    const [highlightedIds, setHighlightedIds] = useState<number[]>([]);
    const highlightedIdSet = useMemo(() => new Set(highlightedIds), [highlightedIds]);
    const treeSummaries = characteristics?.tree_summaries;

    // Fetches node characteristics (height, depth, cost access flag) for both trees
    const refreshCharacteristics = useCallback(async () => {
        const result = await treeCharacteristicsService.get();
        if (result.ok && result.trees) {
            setCharacteristics(result);
            setCharacteristicsLimit(result.limit ?? null);
            setCharacteristicsError(null);
        } else {
            setCharacteristicsError(result.reason ?? "No fue posible cargar las características.");
            setCharacteristicsLimit(null);
        }
    }, []);

    // Fetches observatory data (both tree structures) and characteristics
    const fetchData = useCallback(async () => {
        try {
            const observatory = await ObservatoryService.getObservatory();
            if (!observatory) {
                setError("No se pudo cargar los árboles.");
                return;
            }
            setData(observatory);
            setError(null);
            await refreshCharacteristics();
        } catch (fetchError) {
            console.error("Error obteniendo observatorio (pages)", fetchError);
            setError("No se pudo cargar los árboles.");
        }
    }, [refreshCharacteristics]);

    // Loads observatory on mount
    useEffect(() => {
        void fetchData();
    }, [fetchData]);

    // Refetches after archive operations complete
    useEffect(() => {
        return actionStackService.subscribeToUpdates((payload) => {
            if (payload.actionType === "ARCHIVE_BRANCH") void fetchData();
        });
    }, [fetchData]);

    // Applies incoming socket operations to both trees via patches; refreshes characteristics
    const applyOperation = useCallback((operation: TreeOperation) => {
        void refreshCharacteristics();
        setData((current) => {
            if (!current || current.scenario_id !== operation.scenarioId) return current;
            return operation.steps.reduce((next, step) => ({
                ...next,
                avl_tree: applyTreePatch(next.avl_tree, step.avlPatch, operation.event),
                bst_tree: step.bstPatch
                    ? applyTreePatch(next.bst_tree, step.bstPatch, operation.event)
                    : next.bst_tree,
            }), current);
        });
    }, [refreshCharacteristics]);

    // Subscribes to real-time tree operations and applies them
    useObservatorySocket(applyOperation);

    // Refetches all data after subtree archival
    const refreshAfterArchive = useCallback(async () => {
        await fetchData();
    }, [fetchData]);

    return (
        <section className="min-h-screen space-y-8 overflow-y-auto p-8">
            {error ? (
                <p className="text-red-600" role="alert">{error}</p>
            ) : !data ? (
                <p>Cargando árboles…</p>
            ) : (
                <>
                    <h1 className="text-3xl font-bold text-gray-900">Visualizar eventos</h1>
                    {/* Summary cards: root, height, max depth, leaves for each tree */}
                    {treeSummaries && (
                        <div className="grid gap-4 md:grid-cols-2">
                            {(["avl", "bst"] as const).map((name) => {
                                const summary = treeSummaries[name];
                                return (
                                    <article key={name} className="rounded-xl border border-slate-200 bg-white p-4">
                                        <h2 className="font-semibold text-slate-900">Resumen {name.toUpperCase()}</h2>
                                        <p className="mt-2 text-sm text-slate-600">
                                            Raíz: {summary.root_id ?? "árbol vacío"} · Altura: {summary.height} · Profundidad máxima: {summary.max_depth} · Hojas: {summary.leaves}
                                        </p>
                                    </article>
                                );
                            })}
                        </div>
                    )}
                    {/* Toggle button for node characteristics display with explanatory text */}
                    <div className="flex flex-wrap items-center gap-3">
                        <button
                            type="button"
                            onClick={() => setShowCharacteristics((visible) => !visible)}
                            disabled={!characteristics}
                            aria-pressed={showCharacteristics}
                            className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${showCharacteristics ? "bg-[#0b6e69] text-white" : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"}`}
                        >
                            <Info size={17} />{showCharacteristics ? "Ocultar características AVL" : "Ver características del AVL"}
                        </button>
                        {showCharacteristics && <p className="text-sm text-slate-500">Altura en aristas (hoja = 0) · Profundidad desde la raíz (raíz = 0) · Acceso costoso: prioridad 3 y profundidad &gt; L ({characteristicsLimit ?? "…"}).</p>}
                        {characteristicsError && <p className="text-sm text-amber-700" role="status">{characteristicsError}</p>}
                    </div>
                    {/* Archive subtree panel with highlight synchronization */}
                    <ArchiveTreePanel
                        onPreviewChange={setHighlightedIds}
                        onArchived={refreshAfterArchive}
                    />
                    {/* AVL tree visualization with optional characteristics overlay */}
                    <div>
                        <h2 className="mb-2 text-xl font-semibold">AVL</h2>
                        <div className="max-h-[70vh] max-w-full overflow-auto rounded-lg border border-gray-200 bg-white">
                            <div className="w-max min-w-full p-4">
                                <TreeView data={data.avl_tree} type="avl" highlightIds={highlightedIdSet} showCharacteristics={showCharacteristics} characteristics={characteristics?.trees?.avl} />
                            </div>
                        </div>
                    </div>
                    {/* BST tree visualization */}
                    <div>
                        <h2 className="mb-2 text-xl font-semibold">BST</h2>
                        <div className="max-h-[70vh] max-w-full overflow-auto rounded-lg border border-gray-200 bg-white">
                            <div className="w-max min-w-full p-4">
                                <TreeView data={data.bst_tree} type="bst" highlightIds={highlightedIdSet} />
                            </div>
                        </div>
                    </div>
                </>
            )}
        </section>
    );
};

export default VisualizeTrees;