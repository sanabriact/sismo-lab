import axios from "axios";
import type { SeismicObservatory } from "../../models/SeismicObservatory";

const API_URL = import.meta.env.VITE_API_URL;

class SeismicObservatoryService {

    async getObservatory(): Promise<SeismicObservatory | null> {
        try {
            const response = await axios.get<SeismicObservatory>(`${API_URL}/api/seismic-observatory`);
            return response.data;
        } catch (error) {
            console.error("Error al traer información: " + error)
            return null;
        }
    }
}

export const ObservatoryService = new SeismicObservatoryService()