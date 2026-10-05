// ------------------------------------------------------------------
// E ve nt sT ab le Pr op s
// ------------------------------------------------------------------

import type { SeismicEvent } from "../tree/SeismicEvent";

export interface EventsTableProps {
    data: SeismicEvent[];
    onMarkChecked?: (event: SeismicEvent) => void;
}
