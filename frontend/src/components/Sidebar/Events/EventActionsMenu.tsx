import DropdownMenu from "../DropdownMenu";
import type { DropdownMenuItems } from "../../../models/types/DropdownMenuItems";

const eventActions: DropdownMenuItems[] = [
    {
        label: "Crear evento",
        href: "/create-event"
    },
    {
        label: "Consultar evento",
        href: "/search-event"
    },
    {
        label: "Corregir evento",
        href: "/correct-event"
    },
    {
        label: "Marcar evento",
        href: "/check-event"
    },
    {
        label: "Eliminar evento",
        href: "/delete-event"
    }
];

const EventActionsMenu = () => {
    return (
        <DropdownMenu title="Acciones eventos" items={eventActions} />
    )
}

export default EventActionsMenu;
