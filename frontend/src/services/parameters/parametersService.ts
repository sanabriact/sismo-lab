// ------------------------------------------------------------------
// p ar am et er sS er vi ce
// ------------------------------------------------------------------

import axios from "axios";
import type { ScenarioParameters, ScenarioParametersResponse } from "../../models/interfaces/parameters/ScenarioParameters";

const API_URL = import.meta.env.VITE_API_URL;

class ParametersService {
    // Validates raw form values; returns an error message per invalid field
    validateDraft(values: Record<keyof ScenarioParameters, string>): Partial<Record<keyof ScenarioParameters, string>> {
        const errors: Partial<Record<keyof ScenarioParameters, string>> = {};
        for (const name of ["L", "W", "R", "T"] as const) {
            const raw = values[name].trim();
            const value = Number(raw);
            // Required, numeric, then per-field range rules (L: integer >= 0; others: > 0)
            if (!raw) errors[name] = "Ingresa un valor.";
            else if (!Number.isFinite(value)) errors[name] = "Ingresa un número válido.";
            else if (name === "L" && (!Number.isInteger(value) || value < 0)) errors[name] = "L debe ser un entero mayor o igual a 0.";
            else if (name !== "L" && value <= 0) errors[name] = `${name} debe ser un número mayor que 0.`;
        }
        return errors;
    }

    // Loads current parameters; falls back to a failure response on error
    async get(): Promise<ScenarioParametersResponse> {
        try {
            const response = await axios.get<ScenarioParametersResponse>(`${API_URL}/api/parameters`);
            return response.data;
        } catch (error) {
            // Prefer the server's error body when available
            if (axios.isAxiosError<ScenarioParametersResponse>(error) && error.response?.data) return error.response.data;
            return { ok: false, reason: "No fue posible cargar los parámetros." };
        }
    }

    // Partially updates parameters; falls back to a failure response on error
    async update(parameters: Partial<ScenarioParameters>): Promise<ScenarioParametersResponse> {
        try {
            const response = await axios.patch<ScenarioParametersResponse>(`${API_URL}/api/parameters`, parameters);
            return response.data;
        } catch (error) {
            // Prefer the server's error body when available
            if (axios.isAxiosError<ScenarioParametersResponse>(error) && error.response?.data) return error.response.data;
            return { ok: false, reason: "No fue posible guardar los parámetros." };
        }
    }
}

export const parametersService = new ParametersService();