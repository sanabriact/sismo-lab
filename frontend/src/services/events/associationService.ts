import axios from "axios";
import type { AssociationQueryResponse } from "../../models/interfaces/association/Association";

const API_URL = import.meta.env.VITE_API_URL;

class AssociationService {
    /** Reuse the backend query contract for one event's associations. */
    async getForEvent(eventId: number): Promise<AssociationQueryResponse> {
        try {
            const response = await axios.post<AssociationQueryResponse>(`${API_URL}/api/queries`, {
                type: "associations",
                parameters: { event_id: eventId },
            });
            return response.data;
        } catch {
            return { ok: false, reason: "No fue posible consultar las asociaciones." };
        }
    }
}

export const associationService = new AssociationService();
