// ------------------------------------------------------------------
// H is to ry
// ------------------------------------------------------------------

import { Archive, ChevronRight, FileClock, Hash, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { HistorySummary } from "../../models/interfaces/history/History";
import { historyService } from "../../services/events/historyService";

const History = () => {
    const [summary, setSummary] = useState<HistorySummary | null>(null);

    useEffect(() => {
        void historyService.getSummary().then(setSummary);
    }, []);

    return (
        <section className="mx-auto w-full max-w-5xl space-y-8 px-4 py-10">
            <header>
                <p className="text-sm font-semibold uppercase tracking-wide text-[#0b6e69]">Registro del escenario</p>
                <h1 className="mt-2 text-3xl font-bold text-slate-900">Histórico</h1>
                <p className="mt-2 text-slate-600">Consulta los eventos que ya no forman parte del AVL activo.</p>
            </header>

            {!summary?.ok ? (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-amber-800">{summary?.reason ?? "Cargando histórico..."}</div>
            ) : (
                <div className="grid gap-4 sm:grid-cols-3">
                    <HistoryMetric icon={<Archive size={20} />} label="Eventos archivados" value={summary.archived_events ?? 0} />
                    <HistoryMetric icon={<Trash2 size={20} />} label="Eventos eliminados" value={summary.deleted_events ?? 0} />
                    <HistoryMetric icon={<FileClock size={20} />} label="Identificadores históricos" value={summary.historical_ids ?? 0} />
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-3">
                <HistoryLink to="/history/archived-events" icon={<Archive size={22} />} title="Ver eventos archivados" text="Eventos retirados por archivo de ramas." />
                <HistoryLink to="/history/deleted-events" icon={<Trash2 size={22} />} title="Ver eventos eliminados" text="Eventos retirados mediante eliminación directa." />
                <HistoryLink to="/history/identifiers" icon={<Hash size={22} />} title="Ver identificadores" text="Identificadores registrados por el histórico." />
            </div>
        </section>
    );
};

const HistoryMetric = ({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) => (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-3 text-[#0b6e69]">{icon}<span className="text-sm font-medium text-slate-500">{label}</span></div><p className="mt-3 text-3xl font-bold text-slate-900">{value}</p></div>
);

const HistoryLink = ({ to, icon, title, text }: { to: string; icon: React.ReactNode; title: string; text: string }) => (
    <Link to={to} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-[#0b6e69] hover:shadow-md"><div className="flex items-center gap-3"><div className="rounded-lg bg-[#e7f5f2] p-3 text-[#0b6e69]">{icon}</div><div><h2 className="font-semibold text-slate-900">{title}</h2><p className="mt-1 text-sm text-slate-500">{text}</p></div></div><ChevronRight size={20} className="shrink-0 text-slate-400" /></Link>
);

export default History;
