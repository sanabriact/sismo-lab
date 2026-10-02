import axios from "axios";
import type { SeismicEvent } from "../../models/interfaces/tree/SeismicEvent";

const API_URL = import.meta.env.VITE_API_URL;

class EventService {
    async getAll(): Promise<SeismicEvent[] | null> {
        try {
            const response = await axios.get<SeismicEvent[]>(`${API_URL}/api/events-list`);
            return response.data.events;
        } catch (error) {
            console.log("Error al obtener lista de eventos: " + error);
            return null;
        }
    }
}

export const eventService = new EventService();