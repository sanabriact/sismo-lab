import type { SeismicEvent } from "../tree/SeismicEvent";
import type { Zone } from "./Zone";

export interface SeismicMapProps {
    zones: Zone[];
    events: SeismicEvent[];
    selectedEventId?: number | null;
    onSelectEvent?: (id: number) => void;
}