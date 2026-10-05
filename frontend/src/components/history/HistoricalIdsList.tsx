import type { HistoricalIdsListProps } from "../../models/interfaces/table/HistoricalIdsListProps";

// Grid display of historical event identifiers with responsive columns (2/4/6 based on screen size)
const HistoricalIdsList = ({ identifiers }: HistoricalIdsListProps) => (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        {identifiers.length === 0 ? (
            // Empty state
            <p className="py-8 text-center text-slate-500">No hay identificadores históricos registrados.</p>
        ) : (
            // Responsive grid: 2 cols on mobile, 4 on tablet, 6 on desktop
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 md:grid-cols-6">
                {identifiers.map((identifier) => <div key={identifier} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-center font-semibold text-slate-800">{identifier}</div>)}
            </div>
        )}
    </div>
);

export default HistoricalIdsList;