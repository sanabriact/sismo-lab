import axios from "axios";
import type { ScenarioParameters, ScenarioParametersResponse } from "../../models/interfaces/parameters/ScenarioParameters";

const API_URL = import.meta.env.VITE_API_URL;

class ParametersService {
    validateDraft(values: Record<keyof ScenarioParameters, string>): Partial<Record<keyof ScenarioParameters, string>> {
        const errors: Partial<Record<keyof ScenarioParameters, string>> = {};
        for (const name of ["L", "W", "R", "T"] as const) {
            const raw = values[name].trim();
            const value = Number(raw);
            if (!raw) errors[name] = "Ingresa un valor.";
            else if (!Number.isFinite(value)) errors[name] = "Ingresa un número válido.";
            else if (name === "L" && (!Number.isInteger(value) || value < 0)) errors[name] = "L debe ser un entero mayor o igual a 0.";
            else if (name !== "L" && value <= 0) errors[name] = `${name} debe ser un número mayor que 0.`;
        }
        return errors;
    }

    async get(): Promise<ScenarioParametersResponse> {
        try {
            const response = await axios.get<ScenarioParametersResponse>(`${API_URL}/api/parameters`);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError<ScenarioParametersResponse>(error) && error.response?.data) return error.response.data;
            return { ok: false, reason: "No fue posible cargar los parámetros." };
        }
    }

    async update(parameters: Partial<ScenarioParameters>): Promise<ScenarioParametersResponse> {
        try {
            const response = await axios.patch<ScenarioParametersResponse>(`${API_URL}/api/parameters`, parameters);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError<ScenarioParametersResponse>(error) && error.response?.data) return error.response.data;
            return { ok: false, reason: "No fue posible guardar los parámetros." };
        }
    }
}

export const parametersService = new ParametersService();
