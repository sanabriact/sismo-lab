import axios from "axios";
import type { SeismicObservatory } from "../../models/interfaces/observatory/SeismicObservatory";
import type { SeismicEvent } from "../../models/interfaces/tree/SeismicEvent";

/* Define the API url that connects with backend, via the .env file */
const API_URL = import.meta.env.VITE_API_URL;

class SeismicObservatoryService {

    /* Asynchronous function to return the observatory. */
    async getObservatory(): Promise<SeismicObservatory | null> {
        try {
            const response = await axios.get<SeismicObservatory>(`${API_URL}/api/seismic-observatory`);
            return response.data;
        } catch (error) {
            console.error("Error al traer información: " + error)
            return null;
        }
    }

    async updateObservatory(data: SeismicEvent): Promise<boolean> {
        try {
            await axios.post<SeismicEvent>(`${API_URL}/api/seismic-observatory`);
            return true;
        } catch(error) {
            console.log("Error while updating the observatory: " + error);
            return false
        }
    }
}

/* Export the service as a instance of the class. */
export const ObservatoryService = new SeismicObservatoryService()