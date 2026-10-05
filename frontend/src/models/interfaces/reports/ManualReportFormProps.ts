import type { Station } from "../station/Station";
import type { ReportInput } from "./Report";

export interface ManualReportFormProps {
    stations: Station[];
    simulationTime: string | null;
    loading: boolean;
    onSubmit: (report: ReportInput) => void;
}
