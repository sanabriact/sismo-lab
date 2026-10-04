import axios from "axios";
import type { ArchivedEventsResponse, DeletedEventsResponse, HistoricalIdsResponse, HistorySummary } from "../../models/interfaces/history/History";

const API_URL = import.meta.env.VITE_API_URL;

class HistoryService {
    /** Load the counters displayed by the history landing page. */
    async getSummary(): Promise<HistorySummary> {
        try {
            const response = await axios.get<HistorySummary>(`${API_URL}/api/history`);
            return response.data;
        } catch (error) {
            return this.errorResponse<HistorySummary>(error);
        }
    }

    /** Load only archived events for the dedicated historical view. */
    async getArchivedEvents(): Promise<ArchivedEventsResponse> {
        try {
            const response = await axios.get<ArchivedEventsResponse>(`${API_URL}/api/history/archived-events`);
            return response.data;
        } catch (error) {
            return this.errorResponse<ArchivedEventsResponse>(error);
        }
    }

    /** Load events that were deleted from the active observatory. */
    async getDeletedEvents(): Promise<DeletedEventsResponse> {
        try {
            const response = await axios.get<DeletedEventsResponse>(`${API_URL}/api/history/deleted-events`);
            return response.data;
        } catch (error) {
            return this.errorResponse<DeletedEventsResponse>(error);
        }
    }

    /** Load the identifiers tracked by the historical index. */
    async getHistoricalIds(): Promise<HistoricalIdsResponse> {
        try {
            const response = await axios.get<HistoricalIdsResponse>(`${API_URL}/api/history/identifiers`);
            return response.data;
        } catch (error) {
            return this.errorResponse<HistoricalIdsResponse>(error);
        }
    }

    private errorResponse<T extends { ok: boolean; reason?: string }>(error: unknown): T {
        if (axios.isAxiosError<T>(error) && error.response?.data) {
            return error.response.data;
        }
        return { ok: false, reason: "No fue posible conectar con el servidor." } as T;
    }
}

export const historyService = new HistoryService();
