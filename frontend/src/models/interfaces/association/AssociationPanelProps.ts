import type { AssociationQueryResponse } from "./Association";

export interface AssociationPanelProps {
    eventId: string;
    response: AssociationQueryResponse | null;
    loading: boolean;
    onEventIdChange: (value: string) => void;
    onSearch: () => void;
}