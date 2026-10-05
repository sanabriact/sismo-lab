import { ArrowLeft, FilePlus2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ManualReportForm from "../../components/reports/ManualReportForm";
import type { ReportInput, ReportsResponse } from "../../models/interfaces/reports/Report";
import { reportService } from "../../services/socket/reportService";
import { useObservable } from "../../stores/useObservable";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import { clockStore } from "../../stores/clock/clockStore";

// Page for creating and queueing manual seismic event reports
const CreateReport = () => {
    const navigate = useNavigate();
    const scenario = useObservable(scenarioStore);
    const clock = useObservable(clockStore);
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<ReportsResponse | null>(null);

    // Validates report and enqueues for processing; updates response state with result
    const createReport = async (report: ReportInput) => {
        setLoading(true);
        setResponse(await reportService.createManualReport(report));
        setLoading(false);
    };

    return (
        <section className="mx-auto w-full max-w-4xl space-y-6 p-8">
            <button type="button" onClick={() => navigate("/reports")} className="inline-flex items-center gap-2 text-sm font-medium text-[#04172f] hover:underline"><ArrowLeft size={16} /> Volver a reportes</button>
            <header><div className="flex items-center gap-3"><FilePlus2 className="text-[#0b6e69]" size={25} /><h1 className="text-3xl font-bold text-gray-900">Crear reporte manual</h1></div><p className="mt-2 text-gray-600">El reporte se validará y se agregará a la cola FIFO para su procesamiento.</p></header>
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"><ManualReportForm stations={scenario.stations} simulationTime={clock.currentTime} loading={loading} onSubmit={(report) => void createReport(report)} /></div>
            {/* Result feedback: success message or validation issues */}
            {response && <p className={`rounded-lg p-4 text-sm ${response.ok ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"}`}>{response.ok ? "Reporte creado y añadido a la cola FIFO." : response.issues?.map((issue) => typeof issue === "string" ? issue : issue.reason).join(" ") || "No se pudo crear el reporte."}</p>}
        </section>
    );
};

export default CreateReport;