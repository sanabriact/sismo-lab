import type { SeismicEvent } from "../tree/SeismicEvent";

export interface EventsTableProps {
    data: SeismicEvent[];
    onSearch?: () => void;
    onMarkChecked?: (event: SeismicEvent) => void;
    onDelete?: (event: SeismicEvent) => void;
}