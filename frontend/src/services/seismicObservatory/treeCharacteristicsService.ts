// ------------------------------------------------------------------
// t re eC ha ra ct er is ti cs Se rv ic e
// ------------------------------------------------------------------

import axios from "axios";
import type { TreeCharacteristicsResponse } from "../../models/interfaces/tree/NodeCharacteristics";

const API_URL = import.meta.env.VITE_API_URL;

class TreeCharacteristicsService {
    async get(): Promise<TreeCharacteristicsResponse> {
        try {
            const response = await axios.get<TreeCharacteristicsResponse>(`${API_URL}/api/tree-characteristics`);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError<TreeCharacteristicsResponse>(error) && error.response?.data) return error.response.data;
            return { ok: false, reason: "No fue posible cargar las características de los árboles." };
        }
    }
}

export const treeCharacteristicsService = new TreeCharacteristicsService();
