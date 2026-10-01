import type { SeismicEvent } from "../tree/SeismicEvent";
import type { Zone } from "./Zone";
import type { Station } from "../station/Station";

export interface SeismicMapProps {
    zones: Zone[];
    stations: Station[];
    events: SeismicEvent[];
    selectedEventId?: number | null;
    onSelectEvent?: (id: number) => void;
}
