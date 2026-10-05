import { useState } from "react";
import axios from "axios";
import { Download, FileJson2 } from "lucide-react";
import { jsonExportService } from "../../services/export/jsonExportService";

// Page for downloading a JSON snapshot of the current active scenario
const ExportJson = () => {
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null);

    // Triggers scenario export; extracts backend error reason if axios error, otherwise generic fallback
    const exportJson = async () => {
        if (busy) return;
        setBusy(true);
        setMessage(null);
        try {
            await jsonExportService.download();
            setMessage({ text: "El archivo JSON se descargó correctamente.", error: false });
        } catch (error) {
            const reason = axios.isAxiosError<{ reason?: string }>(error)
                ? error.response?.data?.reason
                : undefined;
            setMessage({ text: reason ?? "No se pudo exportar el escenario. Verifica que el backend esté disponible.", error: true });
        } finally {
            setBusy(false);
        }
    };

    return (
        <section className="mx-auto w-full max-w-5xl space-y-8 px-4 py-10">
            <header>
                <p className="text-sm font-semibold uppercase tracking-wide text-[#0b6e69]">Escenario activo</p>
                <h1 className="mt-2 text-3xl font-bold text-slate-900">Exportar JSON</h1>
                <p className="mt-2 max-w-2xl text-slate-600">Descarga una copia del escenario con su topología, parámetros, estaciones, eventos, historial, reportes, asociaciones y métricas.</p>
            </header>

            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                <div className="flex items-start gap-4">
                    <span className="rounded-xl bg-[#e7f5f2] p-3 text-[#0b6e69]"><FileJson2 size={24} /></span>
                    <div className="flex-1">
                        <h2 className="text-lg font-semibold text-slate-900">Instantánea del escenario</h2>
                        <p className="mt-1 text-sm text-slate-600">El contenido se genera con los datos actuales al momento de exportar y sigue la estructura del esquema JSON de ejemplo.</p>
                        <button type="button" onClick={() => void exportJson()} disabled={busy} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#0b6e69] px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-[#095b57] disabled:cursor-not-allowed disabled:opacity-50">
                            <Download size={18} />{busy ? "Preparando archivo…" : "Descargar JSON"}
                        </button>
                        {message && <p role="status" className={`mt-4 text-sm ${message.error ? "text-red-700" : "text-emerald-700"}`}>{message.text}</p>}
                    </div>
                </div>
            </article>
        </section>
    );
};

export default ExportJson;