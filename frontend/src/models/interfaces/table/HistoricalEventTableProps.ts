import type { ArchivedEvent } from "../history/History";

export interface HistoricalEventsTableProps {
    events: ArchivedEvent[];
    emptyMessage: string;
}
