export interface ArchiveTreePreview {
    root_id: number;
    affected_ids: number[];
    number_nodes: number;
    message: string;
    selection?: {
        afect_ids?: number[];
        number_nodes?: number;
        message?: string;
    };
    subtree: unknown;
}

export interface PrepareArchiveTreeResponse {
    ok: boolean;
    reason?: string;
    tree?: ArchiveTreePreview;
}

export interface ArchiveDecisionResponse {
    ok: boolean;
    reason?: string;
    archived?: boolean;
    subtree?: {
        root_id: number;
        affected_ids: number[];
        number_nodes: number;
    };
}
