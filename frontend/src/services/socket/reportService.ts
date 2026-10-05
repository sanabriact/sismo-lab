import { socketService } from "./socketService";
import type {
    AIReportStartPayload,
    AIReportStatusResponse,
    AIReportStatusEvent,
    AIGeneratedReportsEvent,
    GenerateReportsPayload,
    GenerateReportsResponse,
    ReportQueueEvent,
    ReportQueueSnapshot,
    ReportStepResponse,
    ReportsPayload,
    ReportsResponse,
} from "../../models/interfaces/reports/Report";

const TIMEOUT_MS = 5_000;

class ReportService {
    private emit<T>(event: string, payload: unknown = {}): Promise<T> {
        return new Promise((resolve) => {
            socketService.connect().timeout(TIMEOUT_MS).emit(
                event,
                payload,
                (error: Error | null, response?: T) => {
                    resolve(error || !response ? ({ ok: false, reason: "no_response" } as T) : response);
                },
            );
        });
    }

    enqueueReports(payload: ReportsPayload): Promise<ReportsResponse> {
        return this.emit<ReportsResponse>("reports:prepare", payload).then((response) => (
            response.ok === false && response.reason === "no_response"
                ? { ok: false, enqueued: 0, issues: ["El servidor no respondió."], reason: response.reason }
                : response
        ));
    }

    createManualReport(report: ReportsPayload["reports"][number]): Promise<ReportsResponse> {
        return this.emit<ReportsResponse>("reports:create", report);
    }

    processNext(): Promise<ReportStepResponse> {
        return this.emit<ReportStepResponse>("reports:step");
    }

    startContinuous(): Promise<ReportStepResponse> {
        return this.emit<ReportStepResponse>("reports:start");
    }

    pause(): Promise<ReportStepResponse> {
        return this.emit<ReportStepResponse>("reports:pause");
    }

    getSnapshot(): Promise<ReportQueueSnapshot> {
        return this.emit<ReportQueueSnapshot>("reports:snapshot");
    }

    generateReports(payload: GenerateReportsPayload): Promise<GenerateReportsResponse> {
        return this.emit<GenerateReportsResponse>("reports:generate", payload);
    }

    startAIGeneration(payload: AIReportStartPayload = {}): Promise<AIReportStatusResponse> {
        return this.emit<AIReportStatusResponse>("reports:ai_start", payload);
    }

    stopAIGeneration(): Promise<AIReportStatusResponse> {
        return this.emit<AIReportStatusResponse>("reports:ai_stop");
    }

    getAIGenerationStatus(): Promise<AIReportStatusResponse> {
        return this.emit<AIReportStatusResponse>("reports:ai_status_get");
    }

    subscribeToAIGeneration(
        onStatus: (status: AIReportStatusEvent) => void,
        onGenerated?: (event: AIGeneratedReportsEvent) => void,
        onError?: (payload: { tick?: number; message?: string }) => void,
    ): () => void {
        const socket = socketService.connect();
        socket.on("reports:ai_status", onStatus);
        if (onGenerated) socket.on("reports:generated", onGenerated);
        if (onError) socket.on("reports:generation_error", onError);

        return () => {
            socket.off("reports:ai_status", onStatus);
            if (onGenerated) socket.off("reports:generated", onGenerated);
            if (onError) socket.off("reports:generation_error", onError);
        };
    }

    subscribeToQueue(
        onUpdated: (snapshot: ReportQueueSnapshot) => void,
        onStep: (step: ReportQueueEvent) => void,
        onPaused: () => void,
    ): () => void {
        const socket = socketService.connect();
        socket.on("queue:updated", onUpdated);
        socket.on("queue:step", onStep);
        socket.on("queue:paused", onPaused);

        return () => {
            socket.off("queue:updated", onUpdated);
            socket.off("queue:step", onStep);
            socket.off("queue:paused", onPaused);
        };
    }
}

export const reportService = new ReportService();
