import { useState, type FormEvent } from "react";
import { useObservable } from "../../../stores/useObservable";
import { scenarioStore } from "../../../stores/scenario/ScenarioStore";
import { eventCreationService } from "../../../services/socket/eventCreationService";
import type { EventFormValues } from "../../../models/types/event/EventFormValues";
import EventForm from "../../../components/events/EventsForm";
import type { ManualEventPayload } from "../../../models/interfaces/events/ManualEventPayload";

type View = "options" | "manual";

// Converts ISO datetime to local datetime-local input format; sets seconds to zero to align with simulation clock
const toLocalInputValue = (iso: string) => {
    const value = new Date(iso);
    // datetime-local has no seconds. Use the start of the current minute so
    // the event is not placed after the simulation clock.
    value.setSeconds(0, 0);
    return new Date(value.getTime() - value.getTimezoneOffset() * 60_000)
        .toISOString()
        .slice(0, 16);
};

// Page for creating new seismic events with view toggle between options and manual form
const CreateEvent = () => {
    const scenario = useObservable(scenarioStore);
    const [view, setView] = useState<View>("options");
    const [minimumDatetime, setMinimumDatetime] = useState("");
    const [message, setMessage] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [form, setForm] = useState<EventFormValues>({
        id: "",
        magnitude: "",
        depth: "",
        epicenter_x: "",
        epicenter_y: "",
        datetime: "",
        station: "",
    });

    // Requests server to initialize manual form and receives minimum datetime constraint
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

    // Converts form values to ManualEventPayload and sends to backend for tree insertion
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

    // Options view: selection screen for event creation methods
    if (view === "options") {
        return (
            <section className="p-8">
                <div className="mx-auto max-w-4xl space-y-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Crear evento</h1>
                        <p className="mt-1 text-gray-600">Elige cómo deseas incorporar eventos al escenario activo.</p>
                    </div>
                    <div className="grid gap-5">
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

    // Manual form view: captures event data for insertion into active scenario
    return (
        <section className="p-8">
            <div className="mx-auto max-w-3xl space-y-6">
                <button type="button" onClick={() => setView("options")} className="text-sm font-medium text-[#04172f] hover:underline">← Volver</button>
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Crear evento manual</h1>
                    <p className="mt-1 text-gray-600">La fecha y hora parten del reloj de simulación y no pueden superarlo.</p>
                </div>
                <EventForm
                    mode="create"
                    values={form}
                    stations={scenario.stations}
                    submitting={submitting}
                    minimumDatetime={minimumDatetime}
                    submitText="Crear evento"
                    onChange={setForm}
                    onSubmit={submitManual}
                />

                {message && (
                    <p className="rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
                        {message}
                    </p>
                )}
            </div>
        </section>
    );
};

export default CreateEvent;