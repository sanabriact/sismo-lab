export interface StructureAuditIssue {
    id: number | null;
    type: string;
    message: string;
    stored?: number;
    calculated?: number;
    balance_factor?: number;
}

export interface StructureAuditNodeReport {
    id: number | null;
    issues: StructureAuditIssue[];
    warnings: StructureAuditIssue[];
}

export interface AvlAudit {
    ok: boolean;
    balanced: boolean;
    max_imbalance: number;
    issues: StructureAuditIssue[];
    warnings: StructureAuditIssue[];
    node_reports: StructureAuditNodeReport[];
}

export interface StructureIndicators {
    tree: {
        active_events: number;
        height: number;
        leaves: number;
        inorder: number[];
        preorder: number[];
        postorder: number[];
        levels: number[];
    };
    counters: {
        accepted_corrections: number;
        archived_events: number;
        conflicts: number;
        discarded_reports: number;
        events_by_priority: Record<number, number>;
        high_cost_access_events: number;
        historical_events: number;
        ll_cases: number;
        lr_cases: number;
        mass_archives: number;
        pending_attention: number;
        rl_cases: number;
        rr_cases: number;
        simple_left_rotations: number;
        simple_right_rotations: number;
    };
}

export interface StructureAuditReport {
    mode: "normal" | "stress";
    audit: AvlAudit;
    indicators: StructureIndicators;
}

export interface StructureAuditResponse {
    ok: boolean;
    reason?: "no_scenario";
    report?: StructureAuditReport;
}