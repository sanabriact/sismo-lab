import type { ReportsUploaderProps } from "../../models/interfaces/reports/ReportsUploaderProps";

const ReportsUploader = ({
    selectedFileName,
    error,
}: ReportsUploaderProps) => {
    return (
        <div className="space-y-4">
            {selectedFileName && <p className="text-sm text-gray-600">{selectedFileName}</p>}
            {error && <p className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
        </div>
    );
};

export default ReportsUploader;
