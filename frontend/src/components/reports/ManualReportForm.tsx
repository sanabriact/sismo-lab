// ------------------------------------------------------------------
// M an ua lR ep or tF or m
// ------------------------------------------------------------------

import { useEffect, useState, type FormEvent } from "react";
import type { FormValues } from "../../models/interfaces/reports/FormValues";
import type { ManualReportFormProps } from "../../models/interfaces/reports/ManualReportFormProps";

const emptyValues: FormValues = {
    event_id: "", revision: "1", station: "", magnitude: "", depth: "",
    epicenter_x: "", epicenter_y: "", datetime: "",
};

// Converts ISO datetime to local datetime-local input format, adjusting for timezone offset
const toLocalInputValue = (iso: string) => {
    const value = new Date(iso);
    value.setSeconds(0, 0);
    return new Date(value.getTime() - value.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
};

// Form for manually creating and queueing seismic event reports
const ManualReportForm = ({ stations, simulationTime, loading, onSubmit }: ManualReportFormProps) => {
    const [values, setValues] = useState<FormValues>(emptyValues);

    // Auto-populate datetime field with simulation time on first render
    useEffect(() => {
        if (simulationTime && !values.datetime) {
            setValues((current) => ({ ...current, datetime: toLocalInputValue(simulationTime) }));
        }
    }, [simulationTime, values.datetime]);

    // Updates a single field in the form state
    const update = (field: keyof FormValues, value: string) => {
        setValues((current) => ({ ...current, [field]: value }));
    };

    // Converts string form values to typed ReportInput and sends to parent
    const submit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onSubmit({
            event_id: Number(values.event_id), revision: Number(values.revision), station: Number(values.station),
            magnitude: Number(values.magnitude), depth: Number(values.depth),
            epicenter_x: Number(values.epicenter_x), epicenter_y: Number(values.epicenter_y),
            datetime: new Date(values.datetime).toISOString(),
        });
    };

    const inputClass = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-[#0b6e69] focus:ring-2 focus:ring-[#0b6e69]/15";

    return (
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
            <label className="space-y-1 text-sm font-medium text-slate-700">ID del evento<input required min="1" max="999999" type="number" value={values.event_id} onChange={(event) => update("event_id", event.target.value)} className={inputClass} /></label>
            <label className="space-y-1 text-sm font-medium text-slate-700">Revisión<input required min="1" type="number" value={values.revision} onChange={(event) => update("revision", event.target.value)} className={inputClass} /></label>
            <label className="space-y-1 text-sm font-medium text-slate-700">Estación<select required value={values.station} onChange={(event) => update("station", event.target.value)} className={inputClass}><option value="">Selecciona una estación</option>{stations.map((station) => <option key={station.id} value={station.id}>{station.name} (#{station.id})</option>)}</select></label>
            <label className="space-y-1 text-sm font-medium text-slate-700">Magnitud<input required min="-2" max="10" step="0.1" type="number" value={values.magnitude} onChange={(event) => update("magnitude", event.target.value)} className={inputClass} /></label>
            <label className="space-y-1 text-sm font-medium text-slate-700">Profundidad (km)<input required min="0" max="700" step="0.1" type="number" value={values.depth} onChange={(event) => update("depth", event.target.value)} className={inputClass} /></label>
            <label className="space-y-1 text-sm font-medium text-slate-700">Fecha y hora<input required type="datetime-local" value={values.datetime} onChange={(event) => update("datetime", event.target.value)} className={inputClass} /></label>
            <label className="space-y-1 text-sm font-medium text-slate-700">Epicentro X (km)<input required min="0" max="1000" step="0.1" type="number" value={values.epicenter_x} onChange={(event) => update("epicenter_x", event.target.value)} className={inputClass} /></label>
            <label className="space-y-1 text-sm font-medium text-slate-700">Epicentro Y (km)<input required min="0" max="1000" step="0.1" type="number" value={values.epicenter_y} onChange={(event) => update("epicenter_y", event.target.value)} className={inputClass} /></label>
            <button type="submit" disabled={loading} className="md:col-span-2 rounded-lg bg-[#0b6e69] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#095b57] disabled:cursor-not-allowed disabled:opacity-50">{loading ? "Encolando reporte…" : "Crear y encolar reporte"}</button>
        </form>
    );
};

export default ManualReportForm;