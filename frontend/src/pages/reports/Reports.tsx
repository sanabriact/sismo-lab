import { useEffect, useRef, useState } from "react";
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

const issueText = (issue: ReportsResponse["issues"][number]) => (
    typeof issue === "string" ? issue : `Reporte ${issue.report ?? ""}: ${issue.reason ?? issue.message ?? "problema no especificado"}`
);

const Reports = () => {
    const [fileName, setFileName] = useState<string | null>(null);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [response, setResponse] = useState<ReportsResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [queueSnapshot, setQueueSnapshot] = useState<ReportQueueSnapshot | undefined>();
    const [processing, setProcessing] = useState(false);
    const [processingAction, setProcessingAction] = useState<"step" | "start" | "pause" | null>(null);
    const [stepResult, setStepResult] = useState<ReportStepResponse | null>(null);
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => reportService.subscribeToQueue(
        (nextSnapshot) => {
            setQueueSnapshot(nextSnapshot);
            if (nextSnapshot.size === 0) setProcessing(false);
        },
        (step) => setStepResult({ ok: true, ...step }),
        () => setProcessing(false),
    ), []);

    useEffect(() => {
        void reportService.getSnapshot().then(setQueueSnapshot);
    }, []);

    const selectFile = async (file: File | null) => {
        setResponse(null);
        setStepResult(null);
        setValidationError(null);
        setFileName(file?.name ?? null);
        if (!file) return;

        setLoading(true);
        try {
            const parsed = await parseReportsFile(file);
            const result = await reportService.enqueueReports(parsed);
            setResponse(result);
            setQueueSnapshot(result.snapshot);
        } catch (error) {
            setFileName(null);
            setValidationError(error instanceof Error ? error.message : "No se pudo validar el archivo.");
        } finally {
            setLoading(false);
        }
    };

    const processNext = async () => {
        if (processingAction || !queueSnapshot?.size) return;
        setProcessingAction("step");
        const result = await reportService.processNext();
        setStepResult(result);
        if (!result.ok && result.reason === "empty_queue") setQueueSnapshot({ size: 0, items: [] });
        setProcessingAction(null);
    };

    const startContinuous = async () => {
        if (processingAction || processing || !queueSnapshot?.size) return;
        setProcessingAction("start");
        const result = await reportService.startContinuous();
        setProcessing(result.ok);
        if (!result.ok) setStepResult(result);
        setProcessingAction(null);
    };

    const pauseContinuous = async () => {
        if (processingAction) return;
        setProcessingAction("pause");
        const result = await reportService.pause();
        setProcessing(false);
        if (!result.ok) setStepResult(result);
        setProcessingAction(null);
    };

    const snapshot: ReportQueueSnapshot | undefined = queueSnapshot ?? response?.snapshot;
    const responseReason = (reason?: string) => ({
        no_scenario: "Carga un escenario antes de procesar reportes.",
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

            <div className="grid gap-3 md:grid-cols-3">
                <button type="button" disabled title="La generación con IA estará disponible próximamente" className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-slate-300 disabled:cursor-not-allowed disabled:opacity-60"><Sparkles className="text-violet-500" size={21} /><span><strong className="block text-sm text-slate-900">Generar con IA</strong><small className="text-xs text-slate-500">Próximamente</small></span></button>
                <button type="button" onClick={() => fileInputRef.current?.click()} disabled={loading} className="flex items-center gap-3 rounded-lg border border-[#0b6e69] bg-[#e7f5f2] p-4 text-left shadow-sm transition hover:bg-[#d8efeb] disabled:cursor-not-allowed disabled:opacity-60"><FilePlus2 className="text-[#0b6e69]" size={21} /><span><strong className="block text-sm text-slate-900">Cargar archivo</strong><small className="text-xs text-slate-600">Importar JSON</small></span></button>
                <button type="button" onClick={() => navigate("/reports/create")} className="flex items-center gap-3 rounded-lg bg-[#04172f] p-4 text-left text-white shadow-sm transition hover:bg-[#08264d]"><FilePlus2 size={21} /><span><strong className="block text-sm">Crear manualmente</strong><small className="text-xs text-white/75">Nuevo reporte</small></span></button>
            </div>

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

            {snapshot && (
                <div className="space-y-4">
                    <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <div className="flex items-center gap-2 text-slate-900">
                                <ListChecks className="h-5 w-5 text-[#0b6e69]" aria-hidden="true" />
                                <h2 className="text-xl font-semibold">Cola FIFO</h2>
                            </div>
                            <p className="mt-1 text-sm text-slate-500">
                                {processing ? "Procesamiento continuo activo" : `${snapshot.size} reporte${snapshot.size === 1 ? "" : "s"} pendiente${snapshot.size === 1 ? "" : "s"}`}
                            </p>
                        </div>
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
                                    Pausar
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

                    {stepResult && (
                        <div className={`flex items-start gap-3 rounded-xl border p-4 text-sm ${stepResult.ok ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-red-200 bg-red-50 text-red-800"}`}>
                            {stepResult.ok ? <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" /> : <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />}
                            <div>
                                <p className="font-semibold">{stepResult.ok ? `Reporte procesado: ${stepResult.decision ?? "decisión registrada"}.` : responseReason(stepResult.reason)}</p>
                                {stepResult.ok && <p className="mt-1">Evento {stepResult.eventId} · revisión {stepResult.revision} · quedan {stepResult.remaining ?? 0} en cola.</p>}
                            </div>
                        </div>
                    )}

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
