import type { ChangeEvent } from "react";

interface ReportsUploaderProps {
    selectedFileName: string | null;
    loading?: boolean;
    error?: string | null;
    onFileSelected: (file: File | null) => void;
    onSubmit: () => void;
}

const ReportsUploader = ({
    selectedFileName,
    loading = false,
    error,
    onFileSelected,
    onSubmit,
}: ReportsUploaderProps) => {
    const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
        onFileSelected(event.target.files?.[0] ?? null);
        event.target.value = "";
    };

    return (
        <div className="space-y-4">
            <label className={`inline-block rounded-lg bg-[#04172f] px-4 py-2 text-white ${loading ? "opacity-50" : "cursor-pointer hover:opacity-90"}`}>
                Elegir archivo JSON
                <input
                    type="file"
                    accept=".json,application/json"
                    className="sr-only"
                    disabled={loading}
                    onChange={handleChange}
                />
            </label>
            {selectedFileName && <p className="text-sm text-gray-600">{selectedFileName}</p>}
            {error && <p className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
            <button
                type="button"
                disabled={!selectedFileName || loading}
                onClick={onSubmit}
                className="rounded bg-[#04172f] px-4 py-2 font-medium text-white hover:bg-[#08264d] disabled:cursor-not-allowed disabled:opacity-50"
            >
                {loading ? "Cargando reportes…" : "Cargar reportes"}
            </button>
        </div>
    );
};

export default ReportsUploader;
