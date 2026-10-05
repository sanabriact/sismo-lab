import type { QueryRequest, QueryResponse, QueryType } from "./Query";

export interface QueryPanelProps {
    queryType: QueryType;
    values: Record<string, string>;
    response: QueryResponse | null;
    loading: boolean;
    onTypeChange: (type: QueryType) => void;
    onValueChange: (name: string, value: string) => void;
    onSubmit: (request: QueryRequest) => void;
}
