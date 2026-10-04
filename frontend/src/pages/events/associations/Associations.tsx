import { useEffect, useState, type FormEvent } from "react";
import AssociationPanel from "../../../components/association/AssociationPanel";
import { associationService } from "../../../services/events/associationService";
import type { AssociationLimits, AssociationQueryResponse } from "../../../models/interfaces/association/Association";

const Associations = () => {
    const [eventId, setEventId] = useState("");
    const [limits, setLimits] = useState<AssociationLimits>({ W: 48, R: 40 });
    const [response, setResponse] = useState<AssociationQueryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [savingLimits, setSavingLimits] = useState(false);

    useEffect(() => {
        void associationService.getLimits().then((result) => {
            if (result.ok) setLimits({ W: result.W, R: result.R });
        });
    }, []);

    const search = async () => {
        const numericId = Number(eventId);
        if (!Number.isInteger(numericId) || numericId <= 0) return;
        setLoading(true);
        setResponse(await associationService.getForEvent(numericId));
        setLoading(false);
    };

    const updateLimit = (name: keyof AssociationLimits, value: string) => {
        setLimits((current) => ({ ...current, [name]: Number(value) }));
    };

    const saveLimits = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setSavingLimits(true);
        const result = await associationService.updateLimits(limits);
        if (result.ok) {
            setLimits({ W: result.W, R: result.R });
            if (eventId) await search();
        }
        setSavingLimits(false);
    };

    return (
        <section className="mx-auto w-full max-w-6xl space-y-8 px-4 py-10">
            <header><p className="text-sm font-semibold uppercase tracking-wide text-[#0b6e69]">Relaciones sísmicas</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Asociaciones entre eventos</h1><p className="mt-2 max-w-2xl text-slate-600">Consulta candidatos, referencias seleccionadas y eventos relacionados usando las reglas del escenario.</p></header>
            <AssociationPanel eventId={eventId} limits={limits} response={response} loading={loading} savingLimits={savingLimits} onEventIdChange={setEventId} onLimitChange={updateLimit} onSearch={() => void search()} onSaveLimits={(event) => void saveLimits(event)} />
        </section>
    );
};

export default Associations;
