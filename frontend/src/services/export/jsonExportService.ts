import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

class JsonExportService {
    // Fetches the export JSON and triggers a browser download
    async download(): Promise<void> {
        const response = await axios.get<Record<string, unknown>>(`${API_URL}/api/export/json`);
        // Pretty-print with 2-space indentation
        const content = JSON.stringify(response.data, null, 2);
        // Temporary object URL backed by a JSON blob
        const url = URL.createObjectURL(new Blob([content], { type: "application/json;charset=utf-8" }));
        const link = document.createElement("a");
        link.href = url;
        // Timestamped filename, filesystem-safe (":" and "." replaced)
        link.download = `sismolab-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
        document.body.appendChild(link);
        link.click();
        // Cleanup: remove the link and free the object URL
        link.remove();
        URL.revokeObjectURL(url);
    }
}

export const jsonExportService = new JsonExportService();