import { useCallback, useEffect, useMemo, useState } from "react";
import { ObservatoryService } from "../../../services/seismicObservatory/seismicObservatoryService";
import type { SeismicObservatory } from "../../../models/interfaces/observatory/SeismicObservatory";
import { TreeView } from "../../../components/tree/TreeView";
import { ArchiveTreePanel } from "../../../components/tree/ArchiveTreePanel";
import { useObservatorySocket } from "../../../hooks/socket/useObservatorySocket";
import { applyTreePatch } from "../../../utils/tree/applyTreePatch";
import type { TreeOperation } from "../../../models/interfaces/realTime/TreeOperation";
import { actionStackService } from "../../../services/socket/actionStackService";

const VisualizeTrees = () => {
    const [data, setData] = useState<SeismicObservatory | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [highlightedIds, setHighlightedIds] = useState<number[]>([]);
    const highlightedIdSet = useMemo(() => new Set(highlightedIds), [highlightedIds]);

    const fetchData = useCallback(async () => {
        try {
            const observatory = await ObservatoryService.getObservatory();
            if (!observatory) {
                setError("No se pudo cargar los árboles.");
                return;
            }
            setData(observatory);
            setError(null);
        } catch (fetchError) {
            console.error("Error obteniendo observatorio (pages)", fetchError);
            setError("No se pudo cargar los árboles.");
        }
    }, []);

    useEffect(() => {
        void fetchData();
    }, [fetchData]);

    useEffect(() => {
        return actionStackService.subscribeToUpdates((payload) => {
            if (payload.actionType === "ARCHIVE_BRANCH") void fetchData();
        });
    }, [fetchData]);

    const applyOperation = useCallback((operation: TreeOperation) => {
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
    }, []);

    useObservatorySocket(applyOperation);

    const refreshAfterArchive = useCallback(async () => {
        await fetchData();
    }, [fetchData]);

    return (
        <section className="space-y-8 p-8">
            {error ? (
                <p className="text-red-600" role="alert">{error}</p>
            ) : !data ? (
                <p>Cargando árboles…</p>
            ) : (
                <>
                    <h1 className="text-3xl font-bold text-gray-900">Visualizar eventos</h1>
                    <ArchiveTreePanel
                        onPreviewChange={setHighlightedIds}
                        onArchived={refreshAfterArchive}
                    />
                    <div>
                        <h2 className="mb-2 text-xl font-semibold">AVL</h2>
                        <div className="overflow-auto rounded-lg border border-gray-200">
                            <TreeView data={data.avl_tree} type="avl" highlightIds={highlightedIdSet} />
                        </div>
                    </div>
                    <div>
                        <h2 className="mb-2 text-xl font-semibold">BST</h2>
                        <div className="overflow-auto rounded-lg border border-gray-200">
                            <TreeView data={data.bst_tree} type="bst" highlightIds={highlightedIdSet} />
                        </div>
                    </div>
                </>
            )}
        </section>
    );
};

export default VisualizeTrees;
