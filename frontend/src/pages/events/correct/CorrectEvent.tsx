import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import EventForm from "../../../components/events/EventsForm";
import { useObservable } from "../../../stores/useObservable";
import { scenarioStore } from "../../../stores/scenario/ScenarioStore";
import { eventService } from "../../../services/events/eventService";
import { eventCreationService } from "../../../services/socket/eventCreationService";
import type { EventFormValues } from "../../../models/types/event/EventFormValues";
import type { UpdateEventPayload } from "../../../models/interfaces/events/UpdateEventPayload";

// Converts ISO datetime to local datetime-local input format, adjusting for timezone offset
const toLocalInputValue = (iso: string) => {
    const date = new Date(iso);

    return new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
        .toISOString()
        .slice(0, 16);
};

// Page for editing active seismic events by ID
const CorrectEvent = () => {
    const { eventId } = useParams();
    const navigate = useNavigate();
    const scenario = useObservable(scenarioStore);

    const [form, setForm] = useState<EventFormValues | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    // Fetches event data on mount and populates form with converted datetime
    useEffect(() => {
        const loadEvent = async () => {
            const id = Number(eventId);

            if (!Number.isInteger(id)) {
                setMessage("El identificador del evento no es válido.");
                return;
            }

            const event = await eventService.getEventById(id);

            if (!event) {
                setMessage("El evento no existe o ya no está activo.");
                return;
            }

            setForm({
                id: String(event.key[2]),
                magnitude: String(event.key[1]),
                depth: String(event.depth),
                epicenter_x: String(event.epicenter_x),
                epicenter_y: String(event.epicenter_y),
                datetime: toLocalInputValue(event.datetime),
                station: String(event.reporting_stations[0] ?? ""),
            });
        };

        void loadEvent();
    }, [eventId]);

    // Converts form values to UpdateEventPayload and sends to backend; may queue or execute immediately
    const submitEdit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!form) return;

        setSubmitting(true);
        setMessage(null);

        const payload: UpdateEventPayload = {
            event_id: Number(form.id),
            magnitude: Number(form.magnitude),
            depth: Number(form.depth),
            epicenter_x: Number(form.epicenter_x),
            epicenter_y: Number(form.epicenter_y),
            datetime: new Date(form.datetime).toISOString(),
            station: Number(form.station),
        };

        const response = await eventCreationService.updateManual(payload);

        setSubmitting(false);

        if (!response.ok) {
            setMessage(response.reason ?? "No fue posible actualizar el evento.");
            return;
        }

        setMessage(
            response.queued
                ? `Corrección encolada con revisión ${response.revision}.`
                : `Evento actualizado con revisión ${response.revision}.`,
        );
    };

    return (
        <section className="p-8">
            <div className="mx-auto max-w-3xl space-y-6">
                <button
                    type="button"
                    onClick={() => navigate("/events/list")}
                    className="text-sm font-medium text-[#04172f] hover:underline"
                >
                    ← Volver a gestionar eventos
                </button>

                <div>
                    <h1 className="text-3xl font-bold text-gray-900">
                        Editar evento
                    </h1>
                    <p className="mt-1 text-gray-600">
                        El ID no puede modificarse. Los valores cargados se ven
                        atenuados hasta que los cambies.
                    </p>
                </div>

                {!form ? (
                    <p className="rounded border border-gray-200 bg-white p-4 text-gray-600">
                        {message ?? "Cargando evento…"}
                    </p>
                ) : (
                    <>
                        <EventForm
                            mode="edit"
                            values={form}
                            stations={scenario.stations}
                            submitting={submitting}
                            submitText="Guardar cambios"
                            onChange={setForm}
                            onSubmit={submitEdit}
                        />

                        {message && (
                            <p className="rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
                                {message}
                            </p>
                        )}
                    </>
                )}
            </div>
        </section>
    );
};

export default CorrectEvent;