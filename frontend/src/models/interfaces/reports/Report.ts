// ------------------------------------------------------------------
// R ep or t
// ------------------------------------------------------------------

export interface ReportInput {
    event_id: number;
    revision: number;
    station: number;
    magnitude: number;
    depth: number;
    epicenter_x: number;
    epicenter_y: number;
    datetime: string;
}

export interface ReportsPayload {
    reports: ReportInput[];
}

export interface ReportQueueItem {
    position: number;
    event_id: number;
    revision: number;
    station_id: number;
    magnitude: number;
    depth: number;
    epicenter_x: number;
    epicenter_y: number;
    datetime: string;
}

export interface ReportQueueSnapshot {
    size: number;
    items: ReportQueueItem[];
}

export interface ReportIssue {
    report?: number;
    reason?: string;
    message?: string;
}

export interface ReportsResponse {
    ok: boolean;
    enqueued: number;
    issues: ReportIssue[] | string[];
    snapshot?: ReportQueueSnapshot;
    reason?: string;
}

export interface ReportStepResponse {
    ok: boolean;
    reason?: string;
    decision?: string;
    eventId?: number;
    revision?: number;
    stationId?: number;
    rotations?: string[];
    remaining?: number;
}

export interface ReportQueueEvent {
    decision?: string;
    reason?: string;
    eventId?: number;
    revision?: number;
    stationId?: number;
    rotations?: string[];
    remaining?: number;
}

export interface GenerateReportsPayload {
    count: number;                 // cuántos reportes generar
    scenario?: string;             // prompt/semilla opcional ("ráfaga con altas y antiguos")
    stationIds?: number[];
}

export interface GenerateReportsResponse {
    ok: boolean;
    jobId?: string;
    reason?: string;
}

export interface GeneratedReportEvent {
    jobId: string;
    report: ReportsPayload["reports"][number];
    index: number;
    total: number;
}

export interface AIReportStartPayload {
    intervalSeconds?: number;
    stationIds?: number[];
    scenario?: string;
    seed?: number;
}

export interface AIReportStatusResponse {
    ok: boolean;
    running: boolean;
    alreadyRunning?: boolean;
    reason?: string;
}

export interface AIReportStatusEvent {
    running: boolean;
}

export interface AIGeneratedReportsEvent {
    tick: number;
    reports: ReportsPayload["reports"];
    fallbackCount?: number;
}
