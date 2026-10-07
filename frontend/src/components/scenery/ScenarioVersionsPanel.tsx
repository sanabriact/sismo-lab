import { useState } from "react";
import { useObservable } from "../../stores/useObservable";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import { scenarioService } from "../../services/scenario/ScenarioService";
import { jsonExportService } from "../../services/export/jsonExportService";
import type { ScenarioVersion } from "../../models/interfaces/scenery/ScenarioState";

const ScenarioVersionsPanel = () => {
    const state = useObservable(scenarioStore);
    const [open, setOpen] = useState(false);
    const [pendingVersion, setPendingVersion] = useState<ScenarioVersion | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);

    if (!state.loaded || state.versions.length === 0) return null;

    const load = (version: ScenarioVersion) => {
        setError(null);
        scenarioService.loadVersion(version);
        setPendingVersion(null);
    };

    const selectVersion = async (version: ScenarioVersion) => {
        if (state.operation === "validating") return;
        try {
            const currentSnapshot = await jsonExportService.getSnapshot();
            if (state.versionBaseline && JSON.stringify(currentSnapshot) !== JSON.stringify(state.versionBaseline)) {
                setPendingVersion(version);
                return;
            }
            load(version);
        } catch {
            setError("No se pudo revisar el estado actual. Inténtalo de nuevo.");
        }
    };

    const saveAndLoad = async () => {
        if (!pendingVersion) return;
        setSaving(true);
        setError(null);
        try {
            await jsonExportService.saveVersion();
            load(pendingVersion);
        } catch {
            setError("No se pudieron guardar los cambios. Puedes reintentar o cancelar.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed bottom-5 right-5 z-40">
            <button type="button" onClick={() => setOpen(value => !value)} className="rounded-full bg-[#0b6e69] px-4 py-3 font-semibold text-white shadow-lg hover:bg-[#095b57]">
                Versiones ({state.versions.length})
            </button>
            {open && (
                <section className="absolute bottom-14 right-0 w-[min(24rem,calc(100vw-2rem))] rounded-xl border border-slate-200 bg-white p-4 shadow-xl">
                    <h2 className="text-lg font-semibold text-slate-900">Versiones guardadas</h2>
                    <div className="mt-3 max-h-72 space-y-2 overflow-y-auto">
                        {[...state.versions].sort((a, b) => b.version - a.version).map(version => (
                            <article key={version.version} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 p-3">
                                <div>
                                    <h3 className="font-medium">Versión {version.version}</h3>
                                    {version.saved_at && <time className="text-xs text-slate-500">{new Date(version.saved_at).toLocaleString()}</time>}
                                </div>
                                <button type="button" disabled={state.operation === "validating"} onClick={() => void selectVersion(version)} className="rounded-md bg-[#0b6e69] px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-50">Cargar</button>
                            </article>
                        ))}
                    </div>
                    {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
                </section>
            )}
            {pendingVersion && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4" role="dialog" aria-modal="true" aria-labelledby="unsaved-title">
                    <section className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
                        <h2 id="unsaved-title" className="text-lg font-semibold text-slate-900">Cambios sin guardar</h2>
                        <p className="mt-2 text-sm text-slate-600">¿Deseas guardar los cambios actuales antes de cargar la versión {pendingVersion.version}?</p>
                        {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
                        <div className="mt-5 flex flex-wrap justify-end gap-2">
                            <button type="button" disabled={saving} onClick={() => { setPendingVersion(null); setError(null); }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">Cancelar</button>
                            <button type="button" disabled={saving} onClick={() => load(pendingVersion)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">Descartar cambios</button>
                            <button type="button" disabled={saving} onClick={() => void saveAndLoad()} className="rounded-lg bg-[#0b6e69] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Guardando…" : "Guardar y cargar"}</button>
                        </div>
                    </section>
                </div>
            )}
        </div>
    );
};

export default ScenarioVersionsPanel;
