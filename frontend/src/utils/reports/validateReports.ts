// ------------------------------------------------------------------
// v al id at eR ep or ts
// ------------------------------------------------------------------

import type { ReportInput, ReportsPayload } from "../../models/interfaces/reports/Report";

// Fields every report must include
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

// Type guard: plain object (not null, not an array)
function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

// Type guard: finite number
function isNumber(value: unknown): value is number {
    return typeof value === "number" && Number.isFinite(value);
}

// Checks the value has at most one decimal place
function hasAtMostOneDecimal(value: number): boolean {
    return Math.abs(value * 10 - Math.round(value * 10)) < Number.EPSILON;
}

// Validates one report and returns it typed; throws a descriptive error otherwise
function validateReport(value: unknown, index: number): ReportInput {
    if (!isRecord(value)) throw new Error(`Reporte ${index + 1}: debe ser un objeto.`);

    // All required fields must be present
    const missing = REQUIRED_FIELDS.filter((field) => !(field in value));
    if (missing.length > 0) {
        throw new Error(`Reporte ${index + 1}: faltan campos ${missing.join(", ")}.`);
    }

    // Integer fields
    const integerFields: (keyof ReportInput)[] = ["event_id", "revision", "station"];
    for (const field of integerFields) {
        if (!Number.isInteger(value[field])) {
            throw new Error(`Reporte ${index + 1}: ${field} debe ser entero.`);
        }
    }

    if ((value.revision as number) <= 0) {
        throw new Error(`Reporte ${index + 1}: revision debe ser positiva.`);
    }

    // Numeric fields
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

    // Range and precision checks
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
    // datetime must be parseable as a date
    if (typeof value.datetime !== "string" || Number.isNaN(Date.parse(value.datetime))) {
        throw new Error(`Reporte ${index + 1}: datetime no es una fecha ISO válida.`);
    }

    return value as unknown as ReportInput;
}

// Reads a .json file and returns its validated reports payload
export async function parseReportsFile(file: File): Promise<ReportsPayload> {
    if (!file.name.toLowerCase().endsWith(".json")) {
        throw new Error("Selecciona un archivo con extensión .json.");
    }

    // Parse the file content as JSON
    let parsed: unknown;
    try {
        parsed = JSON.parse(await file.text());
    } catch {
        throw new Error("El archivo no contiene un JSON válido.");
    }

    // Expected shape: { reports: [...] } with at least one item
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