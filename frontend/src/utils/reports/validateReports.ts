// ------------------------------------------------------------------
// v al id at eR ep or ts
// ------------------------------------------------------------------

import type { ReportInput, ReportsPayload } from "../../models/interfaces/reports/Report";

const REQUIRED_FIELDS: (keyof ReportInput)[] = [
    "event_id",
    "revision",
    "station",
    "magnitude",
    "depth",
    "epicenter_x",
    "epicenter_y",
    "datetime",
];

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNumber(value: unknown): value is number {
    return typeof value === "number" && Number.isFinite(value);
}

function hasAtMostOneDecimal(value: number): boolean {
    return Math.abs(value * 10 - Math.round(value * 10)) < Number.EPSILON;
}

function validateReport(value: unknown, index: number): ReportInput {
    if (!isRecord(value)) throw new Error(`Reporte ${index + 1}: debe ser un objeto.`);

    const missing = REQUIRED_FIELDS.filter((field) => !(field in value));
    if (missing.length > 0) {
        throw new Error(`Reporte ${index + 1}: faltan campos ${missing.join(", ")}.`);
    }

    const integerFields: (keyof ReportInput)[] = ["event_id", "revision", "station"];
    for (const field of integerFields) {
        if (!Number.isInteger(value[field])) {
            throw new Error(`Reporte ${index + 1}: ${field} debe ser entero.`);
        }
    }

    if ((value.revision as number) <= 0) {
        throw new Error(`Reporte ${index + 1}: revision debe ser positiva.`);
    }

    const numericFields: (keyof ReportInput)[] = [
        "magnitude",
        "depth",
        "epicenter_x",
        "epicenter_y",
    ];
    for (const field of numericFields) {
        if (!isNumber(value[field])) {
            throw new Error(`Reporte ${index + 1}: ${field} debe ser numérico.`);
        }
    }

    const magnitude = value.magnitude as number;
    const depth = value.depth as number;
    const x = value.epicenter_x as number;
    const y = value.epicenter_y as number;
    if (magnitude < -2 || magnitude > 10 || !hasAtMostOneDecimal(magnitude)) {
        throw new Error(`Reporte ${index + 1}: magnitude fuera de rango o precisión inválida.`);
    }
    if (depth < 0 || depth > 700 || !hasAtMostOneDecimal(depth)) {
        throw new Error(`Reporte ${index + 1}: depth fuera de rango o precisión inválida.`);
    }
    if (x < 0 || x > 1000 || y < 0 || y > 1000) {
        throw new Error(`Reporte ${index + 1}: las coordenadas deben estar entre 0 y 1000.`);
    }
    if (typeof value.datetime !== "string" || Number.isNaN(Date.parse(value.datetime))) {
        throw new Error(`Reporte ${index + 1}: datetime no es una fecha ISO válida.`);
    }

    return value as unknown as ReportInput;
}

export async function parseReportsFile(file: File): Promise<ReportsPayload> {
    if (!file.name.toLowerCase().endsWith(".json")) {
        throw new Error("Selecciona un archivo con extensión .json.");
    }

    let parsed: unknown;
    try {
        parsed = JSON.parse(await file.text());
    } catch {
        throw new Error("El archivo no contiene un JSON válido.");
    }

    if (!isRecord(parsed) || !Array.isArray(parsed.reports)) {
        throw new Error("El JSON debe contener una propiedad reports que sea un array.");
    }
    if (parsed.reports.length === 0) {
        throw new Error("El array reports debe contener al menos un reporte.");
    }

    return {
        reports: parsed.reports.map((report, index) => validateReport(report, index)),
    };
}
