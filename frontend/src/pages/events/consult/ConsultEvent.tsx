import { useState } from "react";
import QueryPanel from "../../../components/query/QueryPanel";
import { queryService } from "../../../services/events/queryService";
import type { QueryRequest, QueryResponse, QueryType } from "../../../models/interfaces/query/Query";

const ConsultEvent = () => {
    const [queryType, setQueryType] = useState<QueryType>("by_id");
    const [values, setValues] = useState<Record<string, string>>({});
    const [response, setResponse] = useState<QueryResponse | null>(null);
    const [loading, setLoading] = useState(false);

    // Keep form values local to the page and send only the selected query fields.
    const updateValue = (name: string, value: string) => {
        setValues((current) => ({ ...current, [name]: value }));
    };

    const changeQueryType = (type: QueryType) => {
        setQueryType(type);
        setValues({});
        setResponse(null);
    };

    const execute = async (request: QueryRequest) => {
        setLoading(true);
        setResponse(await queryService.execute(request));
        setLoading(false);
    };

    return (
        <section className="mx-auto w-full max-w-6xl space-y-8 px-4 py-10">
            <header><p className="text-sm font-semibold uppercase tracking-wide text-[#0b6e69]">Análisis del escenario</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Consultar eventos</h1><p className="mt-2 max-w-2xl text-slate-600">Explora el AVL activo y el histórico con consultas trazables que muestran el costo de búsqueda.</p></header>
            <QueryPanel queryType={queryType} values={values} response={response} loading={loading} onTypeChange={changeQueryType} onValueChange={updateValue} onSubmit={(request) => void execute(request)} />
        </section>
    );
};

export default ConsultEvent;
