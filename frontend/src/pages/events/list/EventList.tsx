// ------------------------------------------------------------------
// E ve nt Li st
// ------------------------------------------------------------------

import { useCallback, useEffect, useMemo, useState } from "react";
import type { SeismicEvent } from "../../../models/interfaces/tree/SeismicEvent";
import { eventService } from "../../../services/events/eventService";
import EventsTable from "../../../components/events/list/EventsTable";

const EventList = () => {
    const [events, setActiveEvents] = useState<SeismicEvent[] | null>(null);

    useEffect(() => {
        getAllActiveEvents();
    }, [])

    const getAllActiveEvents = useCallback(async () => {
        try {
            const activeEvents = await eventService.getAll();
            if (!activeEvents) {
                console.log("No hay eventos activos.")
                return null
            }
            setActiveEvents(activeEvents);
        } catch (error) {
            console.log("No se pudo traer a los eventos activos: " + error);
            return null
        }
    }, [])

    const sortedEvents = useMemo(
        () => [...(events ?? [])].sort((a, b) => a.key[2] - b.key[2]),
        [events]
    );

    return (
        <section className="mx-auto w-full max-w-5xl px-4 py-10">
            <h1 className="mb-6 text-3xl font-bold text-gray-900">Gestionar eventos</h1>
            <EventsTable data={sortedEvents ?? []} />
        </section>
    );
}

export default EventList;