import { Search, Plus, Pencil, Check, Trash2 } from "lucide-react";
import type { EventsTableProps } from "../../../models/interfaces/table/EventsTableProps";
import { useNavigate } from "react-router-dom";
import type { SeismicEvent } from "../../../models/interfaces/tree/SeismicEvent";

const HEADERS = [
    "Identificador",
    "Magnitud",
    "Profundidad",
    "Coordenadas",
    "Fecha y hora",
    "Estaciones",
    "Revisión",
    "Acciones",
];

const formatDateTime = (iso: string) => {
    return new Date(iso).toLocaleString("es-CO", {
        timeZone: "UTC",
        dateStyle: "short",
        timeStyle: "medium",
    }) + " UTC";
};

const iconButton = "rounded-md p-1.5 text-gray-600 transition-colors hover:bg-gray-100";
function EventsTable({
    data,
    onSearch,
    onAdd,
    onEdit,
    onMarkChecked,
    onDelete
}: EventsTableProps) {
    const navigate = useNavigate();

    const handleAdd = () => {
        navigate("/events/create-events");
    };

    const handleEdit = (event: SeismicEvent) => {
        navigate(`/events/correct-event/${event.key[2]}`);
    };

    return (
        <div className="w-full rounded-lg border border-gray-200 bg-white shadow-sm">
            {/* Barra superior: lupa y + a la derecha */}
            <div className="flex items-center justify-end gap-2 border-b border-gray-200 px-4 py-3">
                <button
                    type="button"
                    onClick={onSearch}
                    aria-label="Buscar evento"
                    className={iconButton}
                >
                    <Search size={18} />
                </button>
                <button
                    type="button"
                    onClick={handleAdd}
                    aria-label="Crear evento"
                    className={iconButton}
                >
                    <Plus size={18} />
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                        <tr>
                            {HEADERS.map((header) => (
                                <th key={header} className="px-4 py-3 font-semibold">
                                    {header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {data.length === 0 ? (
                            <tr>
                                <td
                                    colSpan={HEADERS.length}
                                    className="px-4 py-8 text-center text-gray-500"
                                >
                                    No hay eventos activos.
                                </td>
                            </tr>
                        ) : (
                            data.map((event) => (
                                <tr key={event.key[2]} className="hover:bg-gray-50">
                                    <td className="px-4 py-3 font-medium">{event.key[2]}</td>
                                    <td className="px-4 py-3">{event.key[1].toFixed(1)}</td>
                                    <td className="px-4 py-3">{event.depth.toFixed(1)} km</td>
                                    <td className="px-4 py-3">
                                        ({event.epicenter_x.toFixed(1)}, {event.epicenter_y.toFixed(1)})
                                    </td>
                                    <td className="px-4 py-3">{formatDateTime(event.datetime)}</td>
                                    <td className="px-4 py-3">ST-00{event.reporting_stations}</td>
                                    <td className="px-4 py-3">{event.revision}</td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-1">
                                            <button
                                                type="button"
                                                onClick={() => onEdit?.(event)}
                                                aria-label={`Editar evento ${event.key[2]}`}
                                                className={`${iconButton} hover:text-amber-500`}
                                            >
                                                <Pencil size={16} />
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => onMarkChecked?.(event)}
                                                aria-label={`Marcar evento ${event.key[2]} como revisado`}
                                                className={`${iconButton} hover:text-green-600`}
                                            >
                                                <Check size={16} />
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => onDelete?.(event)}
                                                aria-label={`Eliminar evento ${event.key[2]}`}
                                                className={`${iconButton} hover:text-red-600`}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default EventsTable;