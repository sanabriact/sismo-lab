export interface ScenarioParameters {
    L: number;
    W: number;
    R: number;
    T: number;
}

export interface ScenarioParametersResponse extends Partial<ScenarioParameters> {
    ok: boolean;
    changed?: boolean;
    reason?: string;
}
