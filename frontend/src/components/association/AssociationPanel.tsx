import { Link2, Save, Search } from "lucide-react";
import type { FormEvent } from "react";
import type { QueryEvent } from "../../models/interfaces/query/Query";
import type { AssociationLimits, AssociationQueryResponse } from "../../models/interfaces/association/Association";

interface AssociationPanelProps {
    eventId: string;
    limits: AssociationLimits;
    response: AssociationQueryResponse | null;
    loading: boolean;
    savingLimits: boolean;
    onEventIdChange: (value: string) => void;
    onLimitChange: (name: keyof AssociationLimits, value: string) => void;
    onSearch: () => void;
    onSaveLimits: (event: FormEvent<HTMLFormElement>) => void;
}

const EventList = ({ title, events }: { title: string; events: QueryEvent[] }) => (
    <div className="rounded-xl border border-slate-200 p-4">
        <h3 className="font-semibold text-slate-900">{title}</h3>
        {events.length === 0 ? <p className="mt-3 text-sm text-slate-500">No hay eventos.</p> : (
            <div className="mt-3 space-y-2">
                {events.map((event) => (
                    <div key={event.event_id} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                        <span className="font-semibold">Evento {event.event_id}</span>
                        <span className="text-slate-600">M {event.magnitude.toFixed(1)} · {event.event_status}</span>
                    </div>
                ))}
            </div>
        )}
    </div>
);

const AssociationPanel = ({
    eventId,
    limits,
    response,
    loading,
    savingLimits,
    onEventIdChange,
    onLimitChange,
    onSearch,
    onSaveLimits,
}: AssociationPanelProps) => (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <div className="space-y-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-[#e7f5f2] p-2 text-[#0b6e69]"><Link2 size={20} /></div>
                    <div><h2 className="text-lg font-semibold text-slate-900">Consultar relaciones</h2><p className="text-sm text-slate-500">Incluye eventos activos y archivados.</p></div>
                </div>
                <label className="mt-6 block space-y-1 text-sm font-medium text-slate-700">Identificador del evento<input type="number" min="1" value={eventId} onChange={(event) => onEventIdChange(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-[#0b6e69]" /></label>
                <button type="button" onClick={onSearch} disabled={loading || !eventId} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#0b6e69] px-4 py-2.5 font-semibold text-white hover:bg-[#095b57] disabled:cursor-not-allowed disabled:opacity-50"><Search size={18} />{loading ? "Consultando…" : "Consultar asociaciones"}</button>
            </div>

            <form onSubmit={onSaveLimits} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">Reglas de asociación</h2>
                <p className="mt-1 text-sm text-slate-500">Cambiar estos valores recalcula todas las relaciones.</p>
                <div className="mt-4 grid grid-cols-2 gap-3">
                    <label className="space-y-1 text-sm font-medium text-slate-700">W (horas)<input type="number" min="0.1" step="0.1" value={limits.W} onChange={(event) => onLimitChange("W", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
                    <label className="space-y-1 text-sm font-medium text-slate-700">R (km)<input type="number" min="0.1" step="0.1" value={limits.R} onChange={(event) => onLimitChange("R", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
                </div>
                <button type="submit" disabled={savingLimits} className="mt-4 inline-flex items-center gap-2 rounded-lg border border-[#0b6e69] px-4 py-2 text-sm font-semibold text-[#0b6e69] hover:bg-[#e7f5f2] disabled:opacity-50"><Save size={16} />{savingLimits ? "Guardando…" : "Guardar reglas"}</button>
            </form>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Resultado</h2>
            {!response && <p className="mt-6 text-sm text-slate-500">Consulta un evento para ver sus candidatos y referencias.</p>}
            {response && !response.ok && <p className="mt-6 rounded-lg bg-red-50 p-4 text-sm text-red-800">{response.reason}</p>}
            {response?.ok && <div className="mt-4 space-y-4"><p className="text-sm text-slate-600">Ventana: {response.window_hours} horas · Distancia máxima: {response.distance_limit_km} km</p><EventList title="Candidatos a referencia" events={response.candidates ?? []} /><EventList title="Referencia seleccionada" events={response.selected_reference ? [response.selected_reference] : []} /><EventList title="Eventos que lo usan como referencia" events={response.used_by ?? []} /></div>}
        </div>
    </div>
);

export default AssociationPanel;
