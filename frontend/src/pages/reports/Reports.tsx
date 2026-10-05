import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import { AlertCircle, CheckCircle2, FilePlus2, ListChecks, LoaderCircle, Pause, Play, Sparkles, SkipForward } from "lucide-react";
import { useNavigate } from "react-router-dom";
import ReportsUploader from "../../components/reports/ReportsUploader";
import { reportService } from "../../services/socket/reportService";
import { parseReportsFile } from "../../utils/reports/validateReports";
import type {
    ReportQueueSnapshot,
    ReportStepResponse,
    ReportsResponse,
} from "../../models/interfaces/reports/Report";

// Formats issue object as readable string for display
const issueText = (issue: ReportsResponse["issues"][number]) => (
    typeof issue === "string" ? issue : `Reporte ${issue.report ?? ""}: ${issue.reason ?? issue.message ?? "problema no especificado"}`
);

// Page for managing report queue: upload files, AI generation, and processing with FIFO controls
const Reports = () => {
    const [fileName, setFileName] = useState<string | null>(null);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [response, setResponse] = useState<ReportsResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [queueSnapshot, setQueueSnapshot] = useState<ReportQueueSnapshot | undefined>();
    const [processing, setProcessing] = useState(() => reportService.isProcessing());
    const [processingAction, setProcessingAction] = useState<"step" | "start" | "pause" | null>(null);
    const [stepResult, setStepResult] = useState<ReportStepResponse | null>(null);
    const [aiRunning, setAiRunning] = useState(false);
    const [aiAction, setAiAction] = useState<"start" | "stop" | null>(null);
    const [aiError, setAiError] = useState<string | null>(null);
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Subscribes to real-time queue updates, step results, and completion events
    useEffect(() => reportService.subscribeToQueue(
        (nextSnapshot) => {
            setQueueSnapshot(nextSnapshot);
            if (nextSnapshot.size === 0) setProcessing(false);
        },
        (step) => setStepResult({ ok: true, ...step }),
        () => setProcessing(false),
    ), []);

    // Fetches initial queue snapshot on mount
    useEffect(() => {
        void reportService.getSnapshot().then((nextSnapshot) => {
            setQueueSnapshot(nextSnapshot);
            // An empty queue means a previous continuous run has finished.
            if (nextSnapshot.size === 0) setProcessing(false);
        });
    }, []);

    // Subscribes to AI generation status changes and errors; fetches initial status
    useEffect(() => {
        const unsubscribe = reportService.subscribeToAIGeneration(
            ({ running }) => {
                setAiRunning(running);
                if (!running) setAiAction(null);
            },
            () => {
                // The backend already emits queue:updated after enqueueing the AI batch.
                // The generated event is intentionally informational only.
            },
            (payload) => {
                setAiError(payload.message ?? "No se pudo generar el lote de reportes con IA.");
                setAiAction(null);
            },
        );

        void reportService.getAIGenerationStatus().then((status) => {
            if (status.ok) {
                setAiRunning(status.running);
            } else {
                setAiError(status.reason === "no_response"
                    ? "El servidor no respondió al consultar el estado de la IA."
                    : status.reason ?? "No se pudo consultar el estado de la generación con IA.");
            }
        });

        return unsubscribe;
    }, []);

    // Parses JSON file and enqueues reports; updates UI with validation errors or success
    const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        event.target.value = "";
        if (!file) return;

        setFileName(file.name);
        setValidationError(null);
        setResponse(null);
        setLoading(true);

        try {
            const payload = await parseReportsFile(file);
            const result = await reportService.enqueueReports(payload);
            setResponse(result);
            if (result.snapshot) setQueueSnapshot(result.snapshot);
        } catch (error) {
            setValidationError(error instanceof Error ? error.message : "No se pudo leer el archivo.");
        } finally {
            setLoading(false);
        }
    };

    // Toggles AI generation on/off; updates state based on backend response
    const handleAIReportGenerator = async () => {
        if (aiAction) return;

        setAiError(null);
        setAiAction(aiRunning ? "stop" : "start");

        const result = aiRunning
            ? await reportService.stopAIGeneration()
            : await reportService.startAIGeneration();

        if (!result.ok) {
            setAiError(
                result.reason === "no_response"
                    ? "El servidor no respondió al iniciar/detener la generación con IA."
                    : result.reason ?? "No se pudo cambiar el estado de la generación con IA.",
            );
            setAiAction(null);
            return;
        }

        setAiRunning(result.running);
        setAiAction(null);
    };

    // Processes next single report from queue; updates step result with decision or error
    const processNext = async () => {
        if (processingAction || !queueSnapshot?.size) return;
        setProcessingAction("step");
        const result = await reportService.processNext();
        setStepResult(result);
        if (!result.ok && result.reason === "empty_queue") setQueueSnapshot({ size: 0, items: [] });
        setProcessingAction(null);
    };

    // Starts continuous processing of entire queue
    const startContinuous = async () => {
        if (processingAction || processing || !queueSnapshot?.size) return;
        setProcessingAction("start");
        const result = await reportService.startContinuous();
        setProcessing(result.ok);
        if (!result.ok) setStepResult(result);
        setProcessingAction(null);
    };

    // Pauses continuous processing
    const pauseContinuous = async () => {
        if (processingAction) return;
        setProcessingAction("pause");
        const result = await reportService.pause();
        setProcessing(false);
        if (!result.ok) setStepResult(result);
        setProcessingAction(null);
    };

    // Maps backend reason codes to user-facing error messages
    const snapshot: ReportQueueSnapshot | undefined = queueSnapshot ?? response?.snapshot;
    const responseReason = (reason?: string) => ({
        no_scenario: "Carga un escenario antes de procesar reportes.",
        no_valid_stations: "El escenario no tiene estaciones válidas para generar reportes.",
        empty_queue: "No hay reportes pendientes en la cola.",
        already_running: "El procesamiento continuo ya está activo.",
        recovering: "El escenario está ocupado recuperando su estructura.",
        no_response: "El servidor no respondió.",
    }[reason ?? ""] ?? reason ?? "No se pudo completar la operación.");

    return (
        <section className="mx-auto max-w-5xl space-y-8 p-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Reportes</h1>
                <p className="mt-1 text-gray-600">Carga reportes JSON para agregarlos a la cola FIFO.</p>
            </div>

            {/* Action buttons: AI generation, file upload, manual creation */}
            <div className="grid gap-3 md:grid-cols-3">
                <button
                    type="button"
                    onClick={() => void handleAIReportGenerator()}
                    disabled={Boolean(aiAction)}
                    className={`flex items-center gap-3 rounded-lg border p-4 text-left shadow-sm transition disabled:cursor-not-allowed disabled:opacity-60 ${aiRunning ? "border-amber-300 bg-amber-50 hover:bg-amber-100" : "border-slate-200 bg-white hover:bg-gray-200"}`}
                >
                    {aiAction ? <LoaderCircle className="animate-spin text-violet-500" size={21} /> : <Sparkles className={aiRunning ? "text-amber-500" : "text-violet-500"} size={21} />}
                    <span>
                        <strong className="block text-sm text-slate-900">{aiRunning ? "Detener generación IA" : "Generar con IA"}</strong>
                        <small className="text-xs text-slate-500">{aiRunning ? "Generación automática activa" : "Iniciar generación automática"}</small>
                    </span>
                </button>
                <button type="button" onClick={() => fileInputRef.current?.click()} disabled={loading} className="flex items-center gap-3 rounded-lg border border-[#0b6e69] bg-[#e7f5f2] p-4 text-left shadow-sm transition hover:bg-[#d8efeb] disabled:cursor-not-allowed disabled:opacity-60"><FilePlus2 className="text-[#0b6e69]" size={21} /><span><strong className="block text-sm text-slate-900">Cargar archivo</strong><small className="text-xs text-slate-600">Importar JSON</small></span></button>
                <button type="button" onClick={() => navigate("/reports/create")} className="flex items-center gap-3 rounded-lg bg-[#04172f] p-4 text-left text-white shadow-sm transition hover:bg-[#08264d]"><FilePlus2 size={21} /><span><strong className="block text-sm">Crear manualmente</strong><small className="text-xs text-white/75">Nuevo reporte</small></span></button>
            </div>

            {/* Hidden file input for JSON upload */}
            <input
                ref={fileInputRef}
                type="file"
                accept=".json,application/json"
                onChange={(event) => void handleFileChange(event)}
                className="hidden"
                aria-label="Seleccionar archivo JSON de reportes"
            />

            <ReportsUploader selectedFileName={fileName} error={validationError} />

            {/* AI error feedback */}
            {aiError && (
                <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
                    {aiError}
                </div>
            )}

            {/* Upload result: shows enqueued count or validation issues */}
            {response && (
                <div className={`space-y-4 rounded-lg border p-6 ${response.ok ? "border-emerald-300 bg-emerald-50 text-emerald-900" : "border-red-300 bg-red-50 text-red-900"}`}>
                    <h2 className="text-xl font-semibold">Resultado</h2>
                    <p>{response.ok ? `Se cargaron ${response.enqueued} reportes en la cola.` : "No se cargaron los reportes."}</p>
                    {response.issues.length > 0 && (
                        <ul className="list-disc space-y-1 pl-5 text-sm">
                            {response.issues.map((issue, index) => <li key={index}>{issueText(issue)}</li>)}
                        </ul>
                    )}
                </div>
            )}

            {/* Queue display with step/continuous processing controls */}
            {snapshot && (
                <div className="space-y-4">
                    <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <div className="flex items-center gap-2 text-slate-900">
                                <ListChecks className="h-5 w-5 text-[#0b6e69]" aria-hidden="true" />
                                <h2 className="text-xl font-semibold">Cola FIFO</h2>
                            </div>
                            <p className="mt-1 text-sm text-slate-500">
                                {processing ? "Procesando la cola" : `${snapshot.size} reporte${snapshot.size === 1 ? "" : "s"} pendiente${snapshot.size === 1 ? "" : "s"}`}
                            </p>
                        </div>
                        {/* Processing control buttons: next step, start/pause continuous */}
                        <div className="flex flex-wrap gap-2">
                            <button
                                type="button"
                                onClick={() => void processNext()}
                                disabled={Boolean(processingAction) || processing || snapshot.size === 0}
                                className="inline-flex items-center gap-2 rounded-lg border border-[#0b6e69] px-3 py-2 text-sm font-semibold text-[#0b6e69] transition hover:bg-[#e7f5f2] disabled:cursor-not-allowed disabled:opacity-45"
                            >
                                {processingAction === "step" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <SkipForward className="h-4 w-4" />}
                                Procesar siguiente
                            </button>
                            {processing ? (
                                <button
                                    type="button"
                                    onClick={() => void pauseContinuous()}
                                    disabled={Boolean(processingAction)}
                                    className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-3 py-2 text-sm font-semibold text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    {processingAction === "pause" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Pause className="h-4 w-4" />}
                                    Detener
                                </button>
                            ) : (
                                <button
                                    type="button"
                                    onClick={() => void startContinuous()}
                                    disabled={Boolean(processingAction) || snapshot.size === 0}
                                    className="inline-flex items-center gap-2 rounded-lg bg-[#0b6e69] px-3 py-2 text-sm font-semibold text-white transition hover:bg-[#095b57] disabled:cursor-not-allowed disabled:opacity-45"
                                >
                                    {processingAction === "start" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                                    Procesar toda la cola
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Step result: shows success with event/revision or error with reason */}
                    {stepResult && (
                        <div className={`flex items-start gap-3 rounded-xl border p-4 text-sm ${stepResult.ok ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-red-200 bg-red-50 text-red-800"}`}>
                            {stepResult.ok ? <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" /> : <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />}
                            <div>
                                <p className="font-semibold">{stepResult.ok ? `Reporte procesado: ${stepResult.decision ?? "decisión registrada"}.` : responseReason(stepResult.reason)}</p>
                                {stepResult.ok && <p className="mt-1">Evento {stepResult.eventId} · revisión {stepResult.revision} · quedan {stepResult.remaining ?? 0} en cola.</p>}
                            </div>
                        </div>
                    )}

                    {/* Queue table: shows pending reports with all attributes */}
                    <div className="overflow-auto rounded-lg border border-gray-200 bg-white">
                        <table className="min-w-full text-left text-sm">
                            <thead className="border-b border-gray-200 bg-gray-50 text-gray-700">
                                <tr>{["Posición", "Event ID", "Revisión", "Estación", "Magnitud", "Profundidad", "Epicentro X", "Epicentro Y", "Fecha"].map((heading) => <th key={heading} className="whitespace-nowrap px-3 py-2 font-semibold">{heading}</th>)}</tr>
                            </thead>
                            <tbody>
                                {snapshot.items.map((item) => (
                                    <tr key={`${item.position}-${item.event_id}-${item.revision}`} className="border-b border-gray-100 last:border-0">
                                        <td className="px-3 py-2">{item.position}</td>
                                        <td className="px-3 py-2">{item.event_id}</td>
                                        <td className="px-3 py-2">{item.revision}</td>
                                        <td className="px-3 py-2">{item.station_id}</td>
                                        <td className="px-3 py-2">{item.magnitude}</td>
                                        <td className="px-3 py-2">{item.depth}</td>
                                        <td className="px-3 py-2">{item.epicenter_x}</td>
                                        <td className="px-3 py-2">{item.epicenter_y}</td>
                                        <td className="whitespace-nowrap px-3 py-2">{item.datetime}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </section>
    );
};

export default Reports;
