// ------------------------------------------------------------------
// H is to ri ca lI ds
// ------------------------------------------------------------------

import { ArrowLeft, Hash } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import HistoricalIdsList from "../../components/history/HistoricalIdsList";
import { historyService } from "../../services/events/historyService";

// Page displaying all event IDs the observatory has ever recorded
const HistoricalIds = () => {
    const [identifiers, setIdentifiers] = useState<number[]>([]);
    const [message, setMessage] = useState("Cargando identificadores históricos...");

    // Fetches historical IDs on mount; message shows loading state or error
    useEffect(() => {
        void historyService.getHistoricalIds().then((response) => {
            if (!response.ok) {
                setMessage(response.reason ?? "No se pudieron cargar los identificadores históricos.");
                return;
            }
            setIdentifiers(response.identifiers ?? []);
            setMessage("");
        });
    }, []);

    return (
        <section className="mx-auto w-full max-w-6xl space-y-8 px-4 py-10">
            <header className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm font-semibold uppercase tracking-wide text-[#0b6e69]">Histórico</p><h1 className="mt-2 flex items-center gap-3 text-3xl font-bold text-slate-900"><Hash size={28} className="text-[#0b6e69]" />Identificadores históricos</h1><p className="mt-2 text-slate-600">Consulta los identificadores que el observatorio ha registrado.</p></div><Link to="/history" className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-[#0b6e69] hover:text-[#0b6e69]"><ArrowLeft size={17} /> Volver al histórico</Link></header>
            {message && <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">{message}</div>}
            {!message && <HistoricalIdsList identifiers={identifiers} />}
        </section>
    );
};

export default HistoricalIds;