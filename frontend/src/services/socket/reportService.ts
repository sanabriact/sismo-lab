// ------------------------------------------------------------------
// r ep or tS er vi ce
// ------------------------------------------------------------------

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
    // Keep the last known processing state outside the page component.
    // This survives navigation because the service is a shared singleton.
    private processing = false;

    // Emits a socket event; on timeout resolves { ok: false, reason: "no_response" }
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

    // Queues a batch of reports; adds a friendly message on no response
    enqueueReports(payload: ReportsPayload): Promise<ReportsResponse> {
        return this.emit<ReportsResponse>("reports:prepare", payload).then((response) => (
            response.ok === false && response.reason === "no_response"
                ? { ok: false, enqueued: 0, issues: ["El servidor no respondió."], reason: response.reason }
                : response
        ));
    }

    // Creates a single report manually
    createManualReport(report: ReportsPayload["reports"][number]): Promise<ReportsResponse> {
        return this.emit<ReportsResponse>("reports:create", report);
    }

    // Processes the next report in the queue
    processNext(): Promise<ReportStepResponse> {
        return this.emit<ReportStepResponse>("reports:step");
    }

    // Starts continuous queue processing
    startContinuous(): Promise<ReportStepResponse> {
        return this.emit<ReportStepResponse>("reports:start").then((response) => {
            if (response.ok) this.processing = true;
            return response;
        });
    }

    // Pauses queue processing
    pause(): Promise<ReportStepResponse> {
        return this.emit<ReportStepResponse>("reports:pause").then((response) => {
            if (response.ok) this.processing = false;
            return response;
        });
    }

    /** Return the last known continuous-processing state. */
    isProcessing(): boolean {
        return this.processing;
    }

    // Gets the current queue state
    getSnapshot(): Promise<ReportQueueSnapshot> {
        return this.emit<ReportQueueSnapshot>("reports:snapshot");
    }

    // Generates reports from the given parameters
    generateReports(payload: GenerateReportsPayload): Promise<GenerateReportsResponse> {
        return this.emit<GenerateReportsResponse>("reports:generate", payload);
    }

    // Starts automatic AI report generation
    startAIGeneration(payload: AIReportStartPayload = {}): Promise<AIReportStatusResponse> {
        return this.emit<AIReportStatusResponse>("reports:ai_start", payload);
    }

    // Stops AI report generation
    stopAIGeneration(): Promise<AIReportStatusResponse> {
        return this.emit<AIReportStatusResponse>("reports:ai_stop");
    }

    // Gets the current AI generation status
    getAIGenerationStatus(): Promise<AIReportStatusResponse> {
        return this.emit<AIReportStatusResponse>("reports:ai_status_get");
    }

    // Subscribes to AI generation events; returns an unsubscribe function
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

    // Subscribes to queue events; returns an unsubscribe function
    subscribeToQueue(
        onUpdated: (snapshot: ReportQueueSnapshot) => void,
        onStep: (step: ReportQueueEvent) => void,
        onPaused: () => void,
    ): () => void {
        const socket = socketService.connect();
        const handleUpdated = (snapshot: ReportQueueSnapshot) => {
            if (snapshot.size === 0) this.processing = false;
            onUpdated(snapshot);
        };
        const handlePaused = () => {
            this.processing = false;
            onPaused();
        };

        socket.on("queue:updated", handleUpdated);
        socket.on("queue:step", onStep);
        socket.on("queue:paused", handlePaused);

        return () => {
            socket.off("queue:updated", handleUpdated);
            socket.off("queue:step", onStep);
            socket.off("queue:paused", handlePaused);
        };
    }
}

export const reportService = new ReportService();
