import { useEffect, useState, type FormEvent } from "react";
import { Activity, Clock3, MapPin, Save, Settings2 } from "lucide-react";
import { parametersService } from "../../services/parameters/parametersService";
import type { ScenarioParameters } from "../../models/interfaces/parameters/ScenarioParameters";

// Scenario parameters: L (access depth), W (temporal window), R (max distance), T (archive threshold)
const parameterCards: { key: keyof ScenarioParameters; title: string; unit: string; description: string; icon: typeof Activity }[] = [
    { key: "L", title: "Límite de acceso", unit: "niveles", description: "Profundidad límite para identificar accesos costosos en el árbol.", icon: Activity },
    { key: "W", title: "Ventana temporal", unit: "horas", description: "Antigüedad máxima entre eventos para proponer una asociación.", icon: Clock3 },
    { key: "R", title: "Distancia máxima", unit: "km", description: "Distancia epicentral máxima para asociar dos eventos.", icon: MapPin },
    { key: "T", title: "Umbral de archivo", unit: "horas", description: "Antigüedad mínima para proponer archivar una rama del árbol.", icon: Settings2 },
];
type ParameterDraft = Record<keyof ScenarioParameters, string>;

// Page for editing scenario parameters that control associations, queries, and archival logic
const Parameters = () => {
    const [values, setValues] = useState<ParameterDraft | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null);
    // Validates draft values; used for real-time error display and submit button state
    const fieldErrors = values ? parametersService.validateDraft(values) : {};
    const hasErrors = Object.keys(fieldErrors).length > 0;

    // Fetches current parameters on mount; cleanup flag prevents state update after unmount
    useEffect(() => {
        let active = true;
        void parametersService.get().then((result) => {
            if (!active) return;
            if (result.ok && result.L !== undefined && result.W !== undefined && result.R !== undefined && result.T !== undefined) {
                setValues({ L: String(result.L), W: String(result.W), R: String(result.R), T: String(result.T) });
            } else setMessage({ text: result.reason ?? "No se pudieron cargar los parámetros.", error: true });
            setLoading(false);
        });
        return () => { active = false; };
    }, []);

    // Validates draft, sends to backend, and updates local state with confirmed values
    const save = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!values) return;
        const errors = parametersService.validateDraft(values);
        if (Object.keys(errors).length > 0) {
            setMessage({ text: "Corrige los valores marcados antes de guardar.", error: true });
            return;
        }
        setSaving(true);
        setMessage(null);
        const result = await parametersService.update({
            L: Number(values.L),
            W: Number(values.W),
            R: Number(values.R),
            T: Number(values.T),
        });
        if (result.ok && result.L !== undefined && result.W !== undefined && result.R !== undefined && result.T !== undefined) {
            setValues({ L: String(result.L), W: String(result.W), R: String(result.R), T: String(result.T) });
            setMessage({ text: "Parámetros actualizados y aplicados al escenario.", error: false });
        } else setMessage({ text: result.reason ?? "No se pudieron guardar los parámetros.", error: true });
        setSaving(false);
    };

    return (
        <section className="mx-auto w-full max-w-6xl space-y-8 px-4 py-10">
            <header>
                <p className="text-sm font-semibold uppercase tracking-wide text-[#0b6e69]">Configuración del escenario</p>
                <h1 className="mt-2 text-3xl font-bold text-slate-900">Parámetros</h1>
                <p className="mt-2 max-w-2xl text-slate-600">Ajusta las reglas que usan las asociaciones, las consultas y el archivado de árboles.</p>
            </header>

            <form onSubmit={(event) => void save(event)} className="space-y-6">
                {/* Parameter input cards: one per parameter with description, unit, and validation feedback */}
                <div className="grid gap-5 sm:grid-cols-2">
                    {parameterCards.map(({ key, title, unit, description, icon: Icon }) => (
                        <article key={key} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
                            <div className="flex items-start gap-4">
                                <span className="rounded-xl bg-[#e7f5f2] p-3 text-[#0b6e69]"><Icon size={21} /></span>
                                <div className="min-w-0 flex-1">
                                    <div className="flex items-center justify-between gap-3">
                                        <h2 className="font-semibold text-slate-900">{title}</h2>
                                        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">{key}</span>
                                    </div>
                                    <p className="mt-1 min-h-10 text-sm text-slate-500">{description}</p>
                                    <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                                        Valor ({unit})
                                        <input type="number" step="any" value={values?.[key] ?? ""} disabled={loading || saving || !values} aria-invalid={Boolean(fieldErrors[key])} aria-describedby={fieldErrors[key] ? `parameter-${key}-error` : undefined} onChange={(event) => { setValues((current) => current ? { ...current, [key]: event.target.value } : current); setMessage(null); }} className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-lg font-semibold normal-case tracking-normal text-slate-900 outline-none transition focus:border-[#0b6e69] focus:ring-2 focus:ring-[#0b6e69]/15 disabled:bg-slate-50" />
                                        {fieldErrors[key] && <span id={`parameter-${key}-error`} className="mt-1 block text-xs font-medium normal-case tracking-normal text-red-700">{fieldErrors[key]}</span>}
                                    </label>
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
                {/* Submit button with status message: shows loading, saving, or validation error state */}
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    {message ? <p role="status" className={`text-sm ${message.error ? "text-red-700" : "text-emerald-700"}`}>{message.text}</p> : <p className="text-sm text-slate-500">Los cambios se guardan en el escenario activo.</p>}
                    <button type="submit" disabled={loading || saving || !values || hasErrors} className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#0b6e69] px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-[#095b57] disabled:cursor-not-allowed disabled:opacity-50"><Save size={18} />{loading ? "Cargando…" : saving ? "Guardando…" : "Guardar parámetros"}</button>
                </div>
            </form>
        </section>
    );
};

export default Parameters;