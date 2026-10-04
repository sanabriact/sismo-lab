import { ArrowLeft, Archive } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ArchivedEventsTable from "../../components/history/ArchivedEventsTable";
import type { ArchivedEvent } from "../../models/interfaces/history/History";
import { historyService } from "../../services/events/historyService";

const ArchivedEvents = () => {
    const [events, setEvents] = useState<ArchivedEvent[]>([]);
    const [message, setMessage] = useState("Cargando eventos archivados...");

    useEffect(() => {
        void historyService.getArchivedEvents().then((response) => {
            if (!response.ok) {
                setMessage(response.reason ?? "No se pudieron cargar los eventos archivados.");
                return;
            }
            setEvents(response.events ?? []);
            setMessage("");
        });
    }, []);

    return (
        <section className="mx-auto w-full max-w-6xl space-y-8 px-4 py-10">
            <header className="flex flex-wrap items-start justify-between gap-4">
                <div><p className="text-sm font-semibold uppercase tracking-wide text-[#0b6e69]">Histórico</p><h1 className="mt-2 flex items-center gap-3 text-3xl font-bold text-slate-900"><Archive size={28} className="text-[#0b6e69]" />Eventos archivados</h1><p className="mt-2 text-slate-600">Consulta los eventos retirados del árbol AVL por archivo de ramas.</p></div>
                <Link to="/history" className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-[#0b6e69] hover:text-[#0b6e69]"><ArrowLeft size={17} /> Volver al histórico</Link>
            </header>
            {message && <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">{message}</div>}
            {!message && <ArchivedEventsTable events={events} />}
        </section>
    );
};

export default ArchivedEvents;
