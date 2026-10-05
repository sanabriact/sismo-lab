import type { SeismicEvent } from "../tree/SeismicEvent";

export interface EventsTableProps {
    data: SeismicEvent[];
    onMarkChecked?: (event: SeismicEvent) => void;
}