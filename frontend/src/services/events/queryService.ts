import axios from "axios";
import type { QueryRequest, QueryResponse } from "../../models/interfaces/query/Query";

const API_URL = import.meta.env.VITE_API_URL;

class QueryService {
    /** Send a read-only query to the backend application boundary. */
    async execute(request: QueryRequest): Promise<QueryResponse> {
        try {
            const response = await axios.post<QueryResponse>(`${API_URL}/api/queries`, request);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError<QueryResponse>(error) && error.response?.data) {
                return error.response.data;
            }

            return {
                ok: false,
                reason: "No fue posible conectar con el servidor.",
            };
        }
    }
}

export const queryService = new QueryService();
