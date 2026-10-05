// ------------------------------------------------------------------
// A rc hi ve dE ve nt sT ab le
// ------------------------------------------------------------------

import type { ArchivedEvent } from "../../models/interfaces/history/History";
import { formatDateTime } from "../../utils/formatDateTime";

interface ArchivedEventsTableProps {
    events: ArchivedEvent[];
}

const ArchivedEventsTable = ({ events }: ArchivedEventsTableProps) => (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                    <th className="px-4 py-3">Identificador</th>
                    <th className="px-4 py-3">Magnitud</th>
                    <th className="px-4 py-3">Profundidad</th>
                    <th className="px-4 py-3">Coordenadas</th>
                    <th className="px-4 py-3">Fecha UTC</th>
                    <th className="px-4 py-3">Revisión</th>
                    <th className="px-4 py-3">Estado</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
                {events.length === 0 ? (
                    <tr><td colSpan={7} className="px-4 py-10 text-center text-slate-500">No hay eventos archivados.</td></tr>
                ) : events.map((event) => (
                    <tr key={event.event_id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-semibold text-slate-900">{event.event_id}</td>
                        <td className="px-4 py-3">{event.magnitude.toFixed(1)}</td>
                        <td className="px-4 py-3">{event.depth.toFixed(1)} km</td>
                        <td className="px-4 py-3">({event.epicenter_x.toFixed(1)}, {event.epicenter_y.toFixed(1)})</td>
                        <td className="whitespace-nowrap px-4 py-3">{formatDateTime(event.datetime)}</td>
                        <td className="px-4 py-3">{event.revision}</td>
                        <td className="px-4 py-3 capitalize">{event.event_status}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);

export default ArchivedEventsTable;
