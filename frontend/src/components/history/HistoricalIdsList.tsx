// ------------------------------------------------------------------
// H is to ri ca lI ds Li st
// ------------------------------------------------------------------

interface HistoricalIdsListProps {
    identifiers: number[];
}

const HistoricalIdsList = ({ identifiers }: HistoricalIdsListProps) => (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        {identifiers.length === 0 ? (
            <p className="py-8 text-center text-slate-500">No hay identificadores históricos registrados.</p>
        ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 md:grid-cols-6">
                {identifiers.map((identifier) => <div key={identifier} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-center font-semibold text-slate-800">{identifier}</div>)}
            </div>
        )}
    </div>
);

export default HistoricalIdsList;
