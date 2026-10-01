import { useState, type FormEvent, type ReactNode } from "react";
import { useObservable } from "../../../stores/useObservable";
import { scenarioStore } from "../../../stores/scenario/ScenarioStore";
import { eventCreationService, type ManualEventPayload } from "../../../services/socket/eventCreationService";

type View = "options" | "manual";

const toLocalInputValue = (iso: string) => {
    const value = new Date(iso);
    // datetime-local no admite segundos: se redondea hacia arriba para que
    // el valor inicial nunca sea anterior a la hora registrada por servidor.
    value.setSeconds(0, 0);
    value.setMinutes(value.getMinutes() + 1);
    return new Date(value.getTime() - value.getTimezoneOffset() * 60_000)
        .toISOString()
        .slice(0, 16);
};

const CreateEvent = () => {
    const scenario = useObservable(scenarioStore);
    const [view, setView] = useState<View>("options");
    const [minimumDatetime, setMinimumDatetime] = useState("");
    const [message, setMessage] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [form, setForm] = useState({
        id: "",
        magnitude: "",
        depth: "",
        epicenter_x: "",
        epicenter_y: "",
        datetime: "",
        station: "",
    });

    const openManualForm = async () => {
        setSubmitting(true);
        setMessage(null);
        const response = await eventCreationService.beginManual();
        setSubmitting(false);
        if (!response.ok || !response.minimumDatetime) {
            setMessage(response.reason ?? "No fue posible preparar el formulario.");
            return;
        }
        const minimum = toLocalInputValue(response.minimumDatetime);
        setMinimumDatetime(minimum);
        setForm((current) => ({ ...current, datetime: minimum }));
        setView("manual");
    };

    const startGeneration = async () => {
        setSubmitting(true);
        setMessage(null);
        const response = await eventCreationService.startGeneration();
        setSubmitting(false);
        setMessage(response.ok
            ? "La generación de reportes con IA está activa. Los árboles se actualizarán en tiempo real."
            : response.reason ?? "No se pudo iniciar la generación.");
    };

    const submitManual = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setSubmitting(true);
        setMessage(null);
        const payload: ManualEventPayload = {
            id: Number(form.id),
            magnitude: Number(form.magnitude),
            depth: Number(form.depth),
            epicenter_x: Number(form.epicenter_x),
            epicenter_y: Number(form.epicenter_y),
            datetime: new Date(form.datetime).toISOString(),
            station: Number(form.station),
        };
        const response = await eventCreationService.createManual(payload);
        setSubmitting(false);
        if (!response.ok) {
            setMessage(response.reason ?? "No fue posible crear el evento.");
            return;
        }
        setMessage("Evento creado. AVL y BST recibieron la actualización en tiempo real.");
        setForm((current) => ({ ...current, id: "", magnitude: "", depth: "", epicenter_x: "", epicenter_y: "" }));
    };

    if (view === "options") {
        return (
            <section className="p-8">
                <div className="mx-auto max-w-4xl space-y-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Crear evento</h1>
                        <p className="mt-1 text-gray-600">Elige cómo deseas incorporar eventos al escenario activo.</p>
                    </div>
                    <div className="grid gap-5 md:grid-cols-2">
                        <button type="button" disabled={submitting} onClick={startGeneration} className="rounded-lg border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:border-[#04172f] hover:shadow-md disabled:opacity-60">
                            <h2 className="text-xl font-semibold text-gray-900">Iniciar generación de reportes, eventos con IA</h2>
                            <p className="mt-2 text-sm text-gray-600">Genera eventos automáticamente desde las estaciones del escenario y actualiza los árboles en vivo.</p>
                        </button>
                        <button type="button" disabled={submitting} onClick={openManualForm} className="rounded-lg bg-[#04172f] p-6 text-left text-white shadow-sm transition hover:bg-[#08264d] disabled:opacity-60">
                            <h2 className="text-xl font-semibold">Crear manualmente</h2>
                            <p className="mt-2 text-sm text-white/80">Registra un evento con sus datos, fecha y una estación vigente.</p>
                        </button>
                    </div>
                    {message && <p className="rounded-lg border border-gray-200 bg-white p-4 text-sm text-gray-700">{message}</p>}
                </div>
            </section>
        );
    }

    return (
        <section className="p-8">
            <div className="mx-auto max-w-3xl space-y-6">
                <button type="button" onClick={() => setView("options")} className="text-sm font-medium text-[#04172f] hover:underline">← Volver</button>
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Crear evento manual</h1>
                    <p className="mt-1 text-gray-600">La fecha y hora deben ser iguales o posteriores a la apertura de este formulario.</p>
                </div>
                <form onSubmit={submitManual} className="grid gap-5 rounded-lg border border-gray-200 bg-white p-6 shadow-sm md:grid-cols-2">
                    <Field label="ID numérico"><input required min="1" max="999999" step="1" type="number" value={form.id} onChange={(e) => setForm({ ...form, id: e.target.value })} /></Field>
                    <Field label="Magnitud"><input required min="-2" max="10" step="0.1" type="number" value={form.magnitude} onChange={(e) => setForm({ ...form, magnitude: e.target.value })} /></Field>
                    <Field label="Profundidad (km)"><input required min="0" max="700" step="0.1" type="number" value={form.depth} onChange={(e) => setForm({ ...form, depth: e.target.value })} /></Field>
                    <Field label="Coordenada X (km)"><input required min="0" max="1000" step="0.1 " type="number" value={form.epicenter_x} onChange={(e) => setForm({ ...form, epicenter_x: e.target.value })} /></Field>
                    <Field label="Coordenada Y (km)"><input required min="0" max="1000" step="0.1" type="number" value={form.epicenter_y} onChange={(e) => setForm({ ...form, epicenter_y: e.target.value })} /></Field>
                    <Field label="Fecha y hora"><input required min={minimumDatetime} type="datetime-local" value={form.datetime} onChange={(e) => setForm({ ...form, datetime: e.target.value })} /></Field>
                    <Field label="Estación"><select required value={form.station} onChange={(e) => setForm({ ...form, station: e.target.value })}><option value="">Selecciona una estación</option>{scenario.stations.map((station) => <option key={station.id} value={station.id}>{station.name} (#{station.id})</option>)}</select></Field>
                    <div className="flex items-end"><button disabled={submitting} type="submit" className="w-full rounded bg-[#04172f] px-4 py-2 font-medium text-white hover:bg-[#08264d] disabled:opacity-60">{submitting ? "Creando…" : "Crear evento"}</button></div>
                    {message && <p className="md:col-span-2 rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">{message}</p>}
                </form>
            </div>
        </section>
    );
};

const Field = ({ label, children }: { label: string; children: ReactNode }) => (
    <label className="grid gap-1 text-sm font-medium text-gray-700">
        {label}
        <span className="[&>input]:w-full [&>input]:rounded [&>input]:border [&>input]:border-gray-300 [&>input]:px-3 [&>input]:py-2 [&>select]:w-full [&>select]:rounded [&>select]:border [&>select]:border-gray-300 [&>select]:px-3 [&>select]:py-2">{children}</span>
    </label>
);

export default CreateEvent;
