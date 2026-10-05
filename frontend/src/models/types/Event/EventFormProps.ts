// ------------------------------------------------------------------
// E ve nt Fo rm Pr op s
// ------------------------------------------------------------------

import type { FormEvent } from "react";
import type { Station } from "../../interfaces/station/Station";
import type { EventFormValues } from "./EventFormValues";

export type EventFormProps = {
    mode: "create" | "edit";
    values: EventFormValues;
    stations: Station[];
    submitting: boolean;
    minimumDatetime?: string;
    submitText: string;
    onChange: (values: EventFormValues) => void;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};