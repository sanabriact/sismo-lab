/* Search, Plus, Pencil, Check and Trash2 are SVG icons imported from the library lucide-react */
import { Search, Plus, Pencil, Check, Trash2 } from "lucide-react";
import Swal from "sweetalert2";
import type { EventsTableProps } from "../../../models/interfaces/table/EventsTableProps";
import { useNavigate } from "react-router-dom";
import type { SeismicEvent } from "../../../models/interfaces/tree/SeismicEvent";
import { eventService } from "../../../services/events/eventService";

/* Here we define the columns headers */
const HEADERS = [
    "Identificador",
    "Magnitud",
    "Profundidad",
    "Coordenadas",
    "Fecha y hora",
    "Estaciones",
    "Revisión",
    "Estado de atención",
    "Acciones",
];

/* Here we format the date time for better visual appearance */
const formatDateTime = (iso: string) => {
    return new Date(iso).toLocaleString("es-CO", {
        timeZone: "UTC",
        dateStyle: "short",
        timeStyle: "medium",
    }) + " UTC";
};

/* We define a common Tailwind CSS classname for all buttons */
const iconButton = "rounded-md p-1.5 text-gray-600 transition-colors hover:bg-gray-100";
function EventsTable({
    data,
    onSearch,
    onMarkChecked,
    onDelete
}: EventsTableProps) {
    const navigate = useNavigate();

    /* Here we define the handlers for the actions that can be made by the user. */
    const handleAdd = () => {
        navigate("/events/create-events");
    };
    const handleEdit = (event: SeismicEvent) => {
        navigate(`/events/correct-event/${event.key[2]}`);
    };
    const handleMarkChecked = async (event: SeismicEvent) => {
        const result = await Swal.fire({
            title: "¿Quieres marcar el siguiente evento como revisado?",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Sí, marcar como revisado",
            cancelButtonText: "Cancelar",
            html: `
                <div style="text-align: left">
                    <p><b>Evento:</b> ${event.key[2]}</p>
                    <p><b>Magnitud:</b> ${event.key[1].toFixed(1)}</p>
                    <p><b>Profundidad:</b> ${event.depth.toFixed(1)} km</p>
                    <p><b>Coordenadas:</b> (${event.epicenter_x.toFixed(1)}, ${event.epicenter_y.toFixed(1)})</p>
                    <p><b>Fecha y hora:</b> ${formatDateTime(event.datetime)}</p>
                    <p><b>Estaciones:</b> ${event.reporting_stations.join(", ")}</p>
                    <p><b>Revisión:</b> ${event.revision}</p>
                </div>
                `,
        });

        if (!result.isConfirmed) return;

        // Aquí recién envías la petición al backend.
        const updatedEvent = await eventService.setAttentionStatus(event.key[2], "reviewed");

        // Avisar a EventList para actualizar el estado local.
        onMarkChecked?.(updatedEvent);

        await Swal.fire({
            title: "Evento marcado como revisado",
            icon: "success",
            confirmButtonText: "Aceptar",
        });
        window.location.reload();
    };

    return (
        <div className="w-full rounded-lg border border-gray-200 bg-white shadow-sm">
            {/* Top bar with search and add at top right of the table */}
            <div className="flex items-center justify-end gap-2 border-b border-gray-200 px-4 py-3">
                <button
                    type="button"
                    onClick={onSearch}
                    aria-label="Buscar evento"
                    className={iconButton}
                >
                    <Search size={18} />
                </button>
                {/* Here is the add button and the handler that will navigate the user to the creation page */}
                <button
                    type="button"
                    onClick={handleAdd}
                    aria-label="Crear evento"
                    className={iconButton}
                >
                    <Plus size={18} />
                </button>
            </div>

            {/* Here we define the div that contains the table and the table itself */}
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
                            /* 
                                For each event, we generate a cell in the table with its 
                                id, magnitude, depth, coordinates, datetime, reporting stations, revision status and actions buttons.
                            */
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
                                    <td className="px-4 py-3">{event.attention_status.toLocaleUpperCase()}</td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-1">
                                            {/* Here is the edit button with its handler. */}
                                            <button
                                                type="button"
                                                onClick={() => handleEdit(event)}
                                                aria-label={`Editar evento ${event.key[2]}`}
                                                className={`${iconButton} hover:text-amber-500`}
                                            >
                                                <Pencil size={16} />
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => handleMarkChecked(event)}
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