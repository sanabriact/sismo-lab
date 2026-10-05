import { socketService } from "../socket/socketService";
import { applyScenarioFailed, applyScenarioPayload, applyScenarioPending } from "../../utils/scenario/ApplyScenario";
import type { ScenarioLoadRequest } from "../../models/types/scenario/ScenarioLoadRequest";
import type { ScenarioLoadedResponse } from "../../models/interfaces/scenery/ScenarioLoadedResponse";
import type { AIScenarioMode } from "../../models/types/scenario/aiScenarioMode";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";

const TIMEOUT_MS = 30_000;
// Backend error codes mapped to user-facing messages
const REASONS: Record<string, string> = {
    no_loaded: "Carga un escenario primero",
    invalid_request: "Solicitud invalida",
    invalid_file: "Tipo de archivo incorrecto",
    invalid_source: "",
    invalid_ai_mode: "Tipo de escenario arrojado por la IA inválido",
    invalid_scenario: "Escenario arrojado no es válido",
    server_error: "El servido falló al procesar el escenario"
}

class ScenarioService {
    // True while a scenario is already being validated
    private isBusy(): boolean {
        return scenarioStore.getSnapshot().operation === "validating";
    }

    // Emits the load request and handles success, failure and timeout
    private sendLoad(request: ScenarioLoadRequest): void {
        socketService.connect().timeout(TIMEOUT_MS).emit(
            "scenario:load", request, (
                error: Error | null, response?: ScenarioLoadedResponse
            ) => {
                // Timeout or empty response
                if (error || !response) {
                    applyScenarioFailed("Se agotó el tiempo de espera al validar el escenario. Verifica que el backend esté activo e inténtalo de nuevo.")
                    return;
                } 

                // Success: apply the loaded scenario
                if( response.ok && response.scenario){
                    void applyScenarioPayload(response.scenario);
                    return;
                }

                // Backend rejected it: show the mapped reason and issues
                applyScenarioFailed(REASONS[response.reason?? ""] ?? "No se cargó el escenario desde el backend.",
                                    response.issues ?? []
                );
            }
        )
    }

    // Reads a file and sends its content to the backend
    async loadFromFile(file: File): Promise<void> {
        if(this.isBusy()) return;
        applyScenarioPending("file")
        try {
            const content = await file.text()
            this.sendLoad({
                source: "file",
                content
            });
        } catch {
            applyScenarioFailed("No se pudo leer el archivo seleccionado")
        }
    }

    // Requests an AI-generated scenario for the given mode
    async loadFromAI(aiMode: AIScenarioMode): Promise<void> {
        if (this.isBusy()) return;
        applyScenarioPending("ai");
        this.sendLoad({
            source: "ai",
            content: aiMode
        });
    }
}

export const scenarioService = new ScenarioService();