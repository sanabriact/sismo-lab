import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

class JsonExportService {
    async download(): Promise<void> {
        const response = await axios.get<Record<string, unknown>>(`${API_URL}/api/export/json`);
        const content = JSON.stringify(response.data, null, 2);
        const url = URL.createObjectURL(new Blob([content], { type: "application/json;charset=utf-8" }));
        const link = document.createElement("a");
        link.href = url;
        link.download = `sismolab-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }
}

export const jsonExportService = new JsonExportService();
