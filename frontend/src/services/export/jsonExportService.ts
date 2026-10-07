// ------------------------------------------------------------------
// j so nE xp or tS er vi ce
// ------------------------------------------------------------------

import axios from "axios";
import { scenarioStore } from "../../stores/scenario/ScenarioStore";
import type { ScenarioVersion } from "../../models/interfaces/scenery/ScenarioState";

const API_URL = import.meta.env.VITE_API_URL;

class JsonExportService {
    async getSnapshot(): Promise<Record<string, unknown>> {
        const response = await axios.get<Record<string, unknown>>(`${API_URL}/api/scenario/snapshot`);
        return response.data;
    }

    async saveVersion(): Promise<ScenarioVersion[]> {
        const response = await axios.get<Record<string, unknown>>(`${API_URL}/api/export/json`);
        const versions = Array.isArray(response.data.versions) ? response.data.versions as ScenarioVersion[] : [];
        const snapshot = versions.at(-1)?.snapshot ?? response.data;
        const current = scenarioStore.getSnapshot();
        scenarioStore.set({ ...current, versions, versionBaseline: snapshot });
        return versions;
    }

    // Fetches the export JSON and triggers a browser download
    async download(): Promise<void> {
        const versions = await this.saveVersion();
        const snapshot = versions.at(-1)?.snapshot;
        const content = JSON.stringify({ ...snapshot, versions }, null, 2);
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
