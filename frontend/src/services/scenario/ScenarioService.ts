import { socketService } from "../socket/socketService";
import { applyScenarioFailed, applyScenarioPayload, applyScenarioPending } from "../../utils/scenario/ApplyScenario";
import type { ScenarioLoadRequest } from "../../models/types/scenario/ScenarioLoadRequest";
import type { ScenarioLoadedResponse } from "../../models/interfaces/scenery/ScenarioLoadedResponse";
import type { AIScenarioMode } from "../../models/types/scenario/aiScenarioMode";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";

const TIMEOUT_MS = 30_000;
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
    private isBusy(): boolean {
        return scenarioStore.getSnapshot().operation === "validating";
    }

    private sendLoad(request: ScenarioLoadRequest): void {
        socketService.connect().timeout(TIMEOUT_MS).emit(
            "scenario:load", request, (
                error: Error | null, response?: ScenarioLoadedResponse
            ) => {
                if (error || !response) {
                    applyScenarioFailed("Se agotó el tiempo de espera al validar el escenario. Verifica que el backend esté activo e inténtalo de nuevo.")
                    return;
                } 

                if( response.ok && response.scenario){
                    void applyScenarioPayload(response.scenario);
                    return;
                }

                applyScenarioFailed(REASONS[response.reason?? ""] ?? "No se cargó el escenario desde el backend.",
                                    response.issues ?? []
                );
            }
        )
    }

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

    loadFromAI(aiMode: AIScenarioMode): void {
        if (this.isBusy()) return;
        applyScenarioPending("ai");
        this.sendLoad({
            source: "ai",
            aiMode
        });
    }
}

export const scenarioService = new ScenarioService();
