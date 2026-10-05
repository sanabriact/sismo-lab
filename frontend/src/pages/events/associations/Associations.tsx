// ------------------------------------------------------------------
// A ss oc ia ti on s
// ------------------------------------------------------------------

import { useState } from "react";
import AssociationPanel from "../../../components/association/AssociationPanel";
import { associationService } from "../../../services/events/associationService";
import type { AssociationQueryResponse } from "../../../models/interfaces/association/Association";

// Page for querying event associations: candidates, selected references, and related events
const Associations = () => {
    const [eventId, setEventId] = useState("");
    const [response, setResponse] = useState<AssociationQueryResponse | null>(null);
    const [loading, setLoading] = useState(false);

    // Validates event ID and queries associations for that event
    const search = async () => {
        const numericId = Number(eventId);
        if (!Number.isInteger(numericId) || numericId <= 0) return;
        setLoading(true);
        setResponse(await associationService.getForEvent(numericId));
        setLoading(false);
    };

    return (
        <section className="mx-auto w-full max-w-6xl space-y-8 px-4 py-10">
            <header><p className="text-sm font-semibold uppercase tracking-wide text-[#0b6e69]">Relaciones sísmicas</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Asociaciones entre eventos</h1><p className="mt-2 max-w-2xl text-slate-600">Consulta candidatos, referencias seleccionadas y eventos relacionados usando las reglas del escenario.</p></header>
            <AssociationPanel eventId={eventId} response={response} loading={loading} onEventIdChange={setEventId} onSearch={() => void search()} />
        </section>
    );
};

export default Associations;