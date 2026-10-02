import axios from "axios";
import type { SeismicEvent } from "../../models/interfaces/tree/SeismicEvent";

/* Import backend URL via the environment file */
const API_URL = import.meta.env.VITE_API_URL;

class EventService {
    /* This is the method for getting all the active events. It will return a list of SeismicEvent or null */
    async getAll(): Promise<SeismicEvent[] | null> {
        try {
            const response = await axios.get<SeismicEvent[]>(`${API_URL}/api/events-list`);
            return response.data.events;
        } catch (error) {
            console.log("Error al obtener lista de eventos: " + error);
            return null;
        }
    }

    /* We define a method for get an event by its id. It will return a SeismicEvent or null */
    async getEventById(eventId: number): Promise<SeismicEvent | null> {
        try {
            const response = await axios.get<SeismicEvent>(`${API_URL}/api/events/${eventId}`);
            return response.data
        } catch (error) {
            console.log("Error al obtener evento por id: " + error);
            return null;
        }
    }

    async setAttentionStatus(eventId: number, attentionStatus: string): Promise<SeismicEvent> {
        const response = await axios.patch<SeismicEvent>(`${API_URL}/api/events/${eventId}/attention-status`, {attention_status: attentionStatus});
        return response.data
    } 
}

export const eventService = new EventService();