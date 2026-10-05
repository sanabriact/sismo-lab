// ------------------------------------------------------------------
// A rc hi ve Tr ee Pa ne l
// ------------------------------------------------------------------

import { useState } from "react";
import { archiveTreeService } from "../../services/socket/archiveTreeService";
import type { ArchiveTreePreview } from "../../models/interfaces/realTime/ArchiveTree";

interface ArchiveTreePanelProps {
    onPreviewChange: (ids: number[]) => void;
    onArchived: () => Promise<void>;
}

// Maps server error codes to user-facing messages
const reasonFor = (reason?: string) => {
    switch (reason) {
        case "nothing_to_archive":
            return "No hay subárboles que cumplan las condiciones para archivar.";
        case "no_scenario":
            return "Primero debes cargar un escenario.";
        case "busy":
            return "El escenario se está recuperando. Inténtalo de nuevo en un momento.";
        case "invalid_threshold":
            return "El umbral de antigüedad configurado no es válido.";
        case "no_pending_archive":
            return "La selección ya no está disponible. Vuelve a buscar un candidato.";
        case "scenario_changed":
        case "tree_changed":
            return "El escenario cambió desde la selección. Busca un candidato nuevo.";
        default:
            return "No se pudo completar la operación de archivo. Inténtalo de nuevo.";
    }
};

// Panel for finding and archiving eligible subtrees from the AVL tree
export function ArchiveTreePanel({ onPreviewChange, onArchived }: ArchiveTreePanelProps) {
    const [preview, setPreview] = useState<ArchiveTreePreview | null>(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);

    // Requests server to find a candidate subtree eligible for archival
    const prepareArchive = async () => {
        setBusy(true);
        setError(null);
        setNotice(null);
        setPreview(null);
        onPreviewChange([]);

        const response = await archiveTreeService.prepare();
        setBusy(false);
        if (!response?.ok || !response.tree) {
            setError(response ? reasonFor(response.reason) : "No hubo respuesta del servidor.");
            return;
        }

        setPreview(response.tree);
        onPreviewChange(response.tree.affected_ids);
    };

    // Confirms or cancels the archive operation; onArchived callback runs after successful archive
    const decideArchive = async (archive: boolean) => {
        if (!preview) return;
        setBusy(true);
        setError(null);

        const response = await archiveTreeService.decide(archive);
        if (!response?.ok || response.archived !== archive) {
            setBusy(false);
            setError(response ? reasonFor(response.reason) : "No hubo respuesta del servidor.");
            return;
        }

        if (!archive) {
            setPreview(null);
            onPreviewChange([]);
            setBusy(false);
            setNotice("Archivo cancelado. El árbol no fue modificado.");
            return;
        }

        const archivedCount = response.subtree?.number_nodes ?? preview.number_nodes;
        setPreview(null);
        onPreviewChange([]);
        setNotice(`Subárbol archivado correctamente (${archivedCount} ${archivedCount === 1 ? "nodo" : "nodos"}).`);
        await onArchived();
        setBusy(false);
    };

    return (
        <section className="space-y-4 rounded-xl border border-amber-200 bg-amber-50 p-5" aria-label="Archivo de subárbol">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">Archivo de subárboles</h2>
                    <p className="text-sm text-gray-700">Busca el mejor candidato elegible en el AVL.</p>
                </div>
                <button
                    type="button"
                    onClick={prepareArchive}
                    disabled={busy || Boolean(preview)}
                    className="rounded-lg bg-amber-600 px-4 py-2 font-semibold text-white transition hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {busy && !preview ? "Buscando…" : "Archivar"}
                </button>
            </div>

            {/* Preview of the selected candidate subtree with confirmation buttons */}
            {preview && (
                <div className="space-y-3 rounded-lg border border-amber-300 bg-white p-4" role="status">
                    <p className="font-semibold text-gray-900">Candidato encontrado</p>
                    <p className="text-sm text-gray-700">
                        El subárbol se puede archivar porque todos sus eventos tienen prioridad baja y
                        antigüedad mayor que el umbral configurado. El AVL lo eligió por las reglas de
                        tamaño y desempate.
                    </p>
                    <p className="text-sm font-medium text-gray-900">
                        Raíz: SIS-{String(preview.root_id).padStart(6, "0")} · Nodos afectados: {preview.number_nodes}
                    </p>
                    <p className="text-sm text-amber-800">Los nodos candidatos aparecen resaltados en amarillo en ambos árboles.</p>
                    <div className="flex flex-wrap gap-3">
                        <button
                            type="button"
                            onClick={() => void decideArchive(true)}
                            disabled={busy}
                            className="rounded-lg bg-emerald-700 px-4 py-2 font-semibold text-white hover:bg-emerald-800 disabled:opacity-60"
                        >
                            {busy ? "Procesando…" : "Sí, archivar subárbol"}
                        </button>
                        <button
                            type="button"
                            onClick={() => void decideArchive(false)}
                            disabled={busy}
                            className="rounded-lg border border-gray-300 bg-white px-4 py-2 font-semibold text-gray-800 hover:bg-gray-50 disabled:opacity-60"
                        >
                            No, cancelar
                        </button>
                    </div>
                </div>
            )}

            {error && <p className="text-sm font-medium text-red-700" role="alert">{error}</p>}
            {notice && <p className="text-sm font-medium text-emerald-800" role="status">{notice}</p>}
        </section>
    );
}