import { Search, SlidersHorizontal } from "lucide-react";
import type { FormEvent } from "react";
import type { QueryRequest, QueryResponse, QueryType } from "../../models/interfaces/query/Query";

interface QueryPanelProps {
    queryType: QueryType;
    values: Record<string, string>;
    response: QueryResponse | null;
    loading: boolean;
    onTypeChange: (type: QueryType) => void;
    onValueChange: (name: string, value: string) => void;
    onSubmit: (request: QueryRequest) => void;
}

const labels: Record<QueryType, string> = {
    by_id: "Buscar por identificador",
    top_pending: "Primeros pendientes",
    magnitude_range: "Rango de magnitud",
    date_depth_range: "Fecha y profundidad",
    expensive_access: "Acceso costoso",
};

const eventIdField = (values: Record<string, string>, onValueChange: QueryPanelProps["onValueChange"]) => (
    <label className="space-y-1 text-sm font-medium text-slate-700">
        Identificador del evento
        <input
            type="number"
            min="1"
            value={values.event_id ?? ""}
            onChange={(event) => onValueChange("event_id", event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none transition focus:border-[#0b6e69] focus:ring-2 focus:ring-[#0b6e69]/15"
            required
        />
    </label>
);

const QueryPanel = ({
    queryType,
    values,
    response,
    loading,
    onTypeChange,
    onValueChange,
    onSubmit,
}: QueryPanelProps) => {
    const submit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const parameters: Record<string, number | string> = {};

        Object.entries(values).forEach(([name, value]) => {
            if (value !== "") parameters[name] = name.includes("date") ? value : Number(value);
        });

        onSubmit({ type: queryType, parameters });
    };

    return (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
            <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-[#e7f5f2] p-2 text-[#0b6e69]"><SlidersHorizontal size={20} /></div>
                    <div>
                        <h2 className="text-lg font-semibold text-slate-900">Parámetros de consulta</h2>
                        <p className="text-sm text-slate-500">Selecciona una operación de solo lectura.</p>
                    </div>
                </div>

                {/* The select is the only control that changes the query shape. */}
                <label className="mt-6 block space-y-1 text-sm font-medium text-slate-700">
                    Tipo de consulta
                    <select
                        value={queryType}
                        onChange={(event) => onTypeChange(event.target.value as QueryType)}
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 outline-none transition focus:border-[#0b6e69] focus:ring-2 focus:ring-[#0b6e69]/15"
                    >
                        {Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                </label>

                {/* Render only the fields required by the selected query. */}
                <div className="mt-4 space-y-4">
                    {queryType === "by_id" && eventIdField(values, onValueChange)}
                    {queryType === "top_pending" && (
                        <label className="space-y-1 text-sm font-medium text-slate-700">Cantidad k<input type="number" min="1" value={values.k ?? ""} onChange={(event) => onValueChange("k", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" required /></label>
                    )}
                    {queryType === "magnitude_range" && (
                        <div className="grid grid-cols-2 gap-3">
                            <label className="space-y-1 text-sm font-medium text-slate-700">Mínimo<input type="number" step="0.1" value={values.minimum ?? ""} onChange={(event) => onValueChange("minimum", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" required /></label>
                            <label className="space-y-1 text-sm font-medium text-slate-700">Máximo<input type="number" step="0.1" value={values.maximum ?? ""} onChange={(event) => onValueChange("maximum", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" required /></label>
                        </div>
                    )}
                    {queryType === "date_depth_range" && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-3">
                                <label className="space-y-1 text-sm font-medium text-slate-700">Desde<input type="date" value={values.start_date ?? ""} onChange={(event) => onValueChange("start_date", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" required /></label>
                                <label className="space-y-1 text-sm font-medium text-slate-700">Hasta<input type="date" value={values.end_date ?? ""} onChange={(event) => onValueChange("end_date", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" required /></label>
                            </div>
                            <label className="space-y-1 text-sm font-medium text-slate-700">Profundidad máxima (km)<input type="number" min="0" step="0.1" value={values.maximum_depth ?? ""} onChange={(event) => onValueChange("maximum_depth", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" required /></label>
                        </div>
                    )}
                    {queryType === "expensive_access" && <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-600">Busca eventos de prioridad alta cuya profundidad supera el límite L configurado en el escenario.</p>}
                </div>

                <button type="submit" disabled={loading} className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#0b6e69] px-4 py-2.5 font-semibold text-white transition hover:bg-[#095b57] disabled:cursor-not-allowed disabled:opacity-60">
                    <Search size={18} /> {loading ? "Consultando…" : "Ejecutar consulta"}
                </button>
            </form>

            <QueryResults response={response} />
        </div>
    );
};

const QueryResults = ({ response }: { response: QueryResponse | null }) => {
    if (!response) return <div className="flex min-h-64 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">Los resultados aparecerán aquí.</div>;
    if (!response.ok) return <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800"><p className="font-semibold">No se pudo ejecutar la consulta.</p><p className="mt-1 text-sm">{response.reason}</p></div>;

    // Single-event responses and list responses share the same compact table.
    const events = response.events ?? (response.event ? [response.event] : []);
    return (
        <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div><h2 className="text-lg font-semibold text-slate-900">Resultados</h2><p className="text-sm text-slate-500">Nodos examinados: {response.examined_nodes ?? 0}</p></div>
                {response.status && <span className="rounded-full bg-[#e7f5f2] px-3 py-1 text-xs font-semibold uppercase text-[#0b6e69]">{response.status}</span>}
            </div>
            {response.selected_reference !== undefined && <p className="text-sm text-slate-600">Candidatos: {response.candidates?.length ?? 0} · Usado como referencia por: {response.used_by?.length ?? 0} evento(s).</p>}
            {events.length === 0 ? <p className="py-8 text-center text-sm text-slate-500">No se encontraron resultados.</p> : <div className="overflow-auto"><table className="min-w-full text-left text-sm"><thead className="border-b border-slate-200 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">ID</th><th className="px-3 py-2">Prioridad</th><th className="px-3 py-2">Magnitud</th><th className="px-3 py-2">Revisión</th><th className="px-3 py-2">Estado</th></tr></thead><tbody>{events.map((event) => <tr key={event.event_id} className="border-b border-slate-100 last:border-0"><td className="px-3 py-3 font-semibold">{event.event_id}</td><td className="px-3 py-3">{event.priority}</td><td className="px-3 py-3">{event.magnitude.toFixed(1)}</td><td className="px-3 py-3">{event.revision}</td><td className="px-3 py-3">{event.event_status}</td></tr>)}</tbody></table></div>}
        </div>
    );
};

export default QueryPanel;
