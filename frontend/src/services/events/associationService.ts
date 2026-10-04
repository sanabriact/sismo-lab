import axios from "axios";
import type {
    AssociationLimits,
    AssociationLimitsResponse,
    AssociationQueryResponse,
} from "../../models/interfaces/association/Association";

const API_URL = import.meta.env.VITE_API_URL;

class AssociationService {
    /** Read the current W and R values from the active scenario. */
    async getLimits(): Promise<AssociationLimitsResponse> {
        try {
            const response = await axios.get<AssociationLimitsResponse>(`${API_URL}/api/associations/limits`);
            return response.data;
        } catch {
            return { ok: false, W: 48, R: 40, reason: "No fue posible obtener los límites." };
        }
    }

    /** Update limits through the Event Engine boundary. */
    async updateLimits(limits: AssociationLimits): Promise<AssociationLimitsResponse> {
        try {
            const response = await axios.patch<AssociationLimitsResponse>(
                `${API_URL}/api/associations/limits`,
                limits,
            );
            return response.data;
        } catch (error) {
            if (axios.isAxiosError<AssociationLimitsResponse>(error) && error.response?.data) {
                return error.response.data;
            }
            return { ok: false, ...limits, reason: "No fue posible actualizar los límites." };
        }
    }

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
